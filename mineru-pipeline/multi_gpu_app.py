#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""=================================================
@PROJECT_NAME: services
@File    : multi_gpu_app.py
@Author  : caixiongjiang
@Date    : 2025/10/23 14:35
@Function: 
    mineru 分布式部署服务端（多GPU）
@Modify History:
         
@Copyright：Copyright(c) 2024-2026. All Rights Reserved
=================================================="""

import os
import json
import gc
import tempfile
import base64
import shutil
import fitz
import filetype
from typing import Tuple

import torch

import litserve as ls
from pathlib import Path
from fastapi import HTTPException
from glob import glob
from base64 import b64encode
from io import StringIO
from loguru import logger

import magic_pdf.model as model_config
from magic_pdf.config.enums import SupportedPdfParseMethod
from magic_pdf.data.data_reader_writer import DataWriter, FileBasedDataWriter
from magic_pdf.data.dataset import PymuDocDataset
from magic_pdf.model.doc_analyze_by_custom_model import doc_analyze
from magic_pdf.tools.cli import convert_file_to_pdf

model_config.__use_inside_model__ = True


class MemoryDataWriter(DataWriter):
    def __init__(self):
        self.buffer = StringIO()

    def write(self, path: str, data: bytes) -> None:
        if isinstance(data, str):
            self.buffer.write(data)
        else:
            self.buffer.write(data.decode("utf-8"))

    def write_string(self, path: str, data: str) -> None:
        self.buffer.write(data)

    def get_value(self) -> str:
        return self.buffer.getvalue()

    def close(self):
        self.buffer.close()


class MinerUAPI(ls.LitAPI):
    def __init__(self, output_dir='/tmp', force_gpu_id=None):
        self.output_dir = Path(output_dir)
        self.force_gpu_id = force_gpu_id  # 强制使用的GPU ID
        super().__init__()

    def setup(self, device):
        """初始化模型，支持多GPU"""
        self.device = device

        logger.info(f'=== Worker Setup on {device} ===')
        logger.info(f'Process ID: {os.getpid()}')
        logger.info(f'CUDA_VISIBLE_DEVICES: {os.environ.get("CUDA_VISIBLE_DEVICES", "Not set")}')

        if torch.cuda.is_available():
            logger.info(f'Available CUDA devices: {torch.cuda.device_count()}')
            logger.info(f'Current device before setup: {torch.cuda.current_device()}')

            # 设置正确的CUDA设备
            if device.startswith('cuda'):
                gpu_id = int(device.split(':')[-1])
                if gpu_id < torch.cuda.device_count():
                    torch.cuda.set_device(gpu_id)
                    logger.info(f'Set device to GPU {gpu_id}')

                    # 验证设备设置
                    current_device = torch.cuda.current_device()
                    logger.info(f'Current device after setup: {current_device}')

                    # 创建测试tensor确认设备
                    test_tensor = torch.tensor([1.0]).cuda()
                    logger.info(f'Test tensor on device: {test_tensor.device}')

        # 初始化模型
        logger.info('Initializing MinerU models...')
        from magic_pdf.model.doc_analyze_by_custom_model import ModelSingleton
        model_manager = ModelSingleton()
        model_manager.get_model(True, True)
        # model_manager.get_model(False, False)

        # 最终验证
        if torch.cuda.is_available():
            final_device = torch.cuda.current_device()
            logger.info(f'Final device after model init: {final_device}')

        logger.info(f'=== Setup Complete on {device} ===')

    def decode_request(self, request, **kwargs):
        """解析请求参数，保持与原接口一致"""
        # 正确解析FormData对象
        file = request.get("file", "")
        params = request.get('kwargs', {})
        params_str = json.dumps(params, ensure_ascii=False, indent=4)

        logger.info(f"params:\n {params_str}")

        return file, {
            "file_name": params.get("file_name", ""),
            "parse_method": params.get("parse_method", "ocr"),
            "start_page_id": int(params.get("start_page_id", 0)),
            "end_page_id": int(params.get("end_page_id")) if params.get("end_page_id") else None,
            "is_json_md_dump": params["is_json_md_dump"].lower() == "false",
            "output_dir": params.get("output_dir", "output"),
            "return_layout": params["return_layout"].lower() == "true",
            "return_info": params["return_info"].lower() == "true",
            "return_content_list": params["return_content_list"].lower() == "true",
            "return_images": params["return_images"].lower() == "true"
        }

    def predict(self, inputs, **kwargs):
        """核心处理逻辑，保持与原逻辑一致"""
        try:
            file, params = inputs[0], inputs[1]
            # 处理文件
            file_name = params['file_name']
            pdf_bytes, pdf_name = self.cvt2pdf(file, file_name)
            is_json_md_dump = params["is_json_md_dump"]
            return_layout = params["return_layout"]
            return_info = params["return_info"]
            return_content_list = params["return_content_list"]
            return_images = params["return_images"]

            # 处理PDF
            output_path = f"{params['output_dir']}/{pdf_name}"
            output_image_path = f"{output_path}/images"
            image_writer = FileBasedDataWriter(output_image_path)

            # 同步处理
            infer_result, pipe_result = self.process_pdf(
                pdf_bytes,
                params["parse_method"],
                image_writer,
                params["start_page_id"],
                params["end_page_id"]
            )

            # 生成响应数据
            return self._build_response(
                infer_result, pipe_result, output_path, output_image_path,
                pdf_name, is_json_md_dump, return_layout, return_info,
                return_content_list, return_images
            )

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            self.clean_memory(self.device)

    def encode_response(self, output, **kwargs):
        """保持与原接口一致的响应格式"""
        return output

    def process_pdf(self, pdf_bytes, parse_method, image_writer, start_page_id, end_page_id):
        """保持与原函数一致的处理逻辑"""
        ds = PymuDocDataset(pdf_bytes)
        if parse_method == "ocr":
            infer_result = ds.apply(doc_analyze, ocr=True, start_page_id=start_page_id, end_page_id=end_page_id)
            pipe_result = infer_result.pipe_ocr_mode(image_writer)
        elif parse_method == "txt":
            infer_result = ds.apply(doc_analyze, ocr=False, start_page_id=start_page_id, end_page_id=end_page_id)
            pipe_result = infer_result.pipe_txt_mode(image_writer)
        else:
            if ds.classify() == SupportedPdfParseMethod.OCR:
                infer_result = ds.apply(doc_analyze, ocr=True, start_page_id=start_page_id, end_page_id=end_page_id)
                pipe_result = infer_result.pipe_ocr_mode(image_writer)
            else:
                infer_result = ds.apply(doc_analyze, ocr=False, start_page_id=start_page_id, end_page_id=end_page_id)
                pipe_result = infer_result.pipe_txt_mode(image_writer)
        return infer_result, pipe_result

    def cvt2pdf(self, file_base64, filename: str) -> Tuple[bytes, str] | None:

        try:
            if not filename:
                raise Exception('No file name provided')
            pdf_name = filename.split('.')[0] + '.pdf'
            temp_dir = Path(tempfile.mkdtemp())
            temp_file = temp_dir.joinpath('tmpfile')
            file_bytes = base64.b64decode(file_base64)
            file_ext = filetype.guess_extension(file_bytes)

            if file_ext in ['pdf', 'jpg', 'png', 'doc', 'docx', 'ppt', 'pptx']:
                if file_ext == 'pdf':
                    return file_bytes, pdf_name
                elif file_ext in ['jpg', 'png']:
                    with fitz.open(stream=file_bytes, filetype=file_ext) as f:
                        return f.convert_to_pdf(), pdf_name
                else:
                    temp_file.write_bytes(file_bytes)
                    convert_file_to_pdf(temp_file, temp_dir)
                    return temp_file.with_suffix('.pdf').read_bytes(), pdf_name
            else:
                raise Exception('Unsupported file format')
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _build_response(self, infer_result, pipe_result, output_path, output_image_path,
                        pdf_name, is_json_md_dump, return_layout, return_info,
                        return_content_list, return_images):
        """构建响应数据结构"""
        # 内存写入器初始化
        content_list_writer = MemoryDataWriter()
        md_content_writer = MemoryDataWriter()
        middle_json_writer = MemoryDataWriter()

        # 数据写入
        pipe_result.dump_content_list(content_list_writer, "", "images")
        pipe_result.dump_md(md_content_writer, "", "images")
        pipe_result.dump_middle_json(middle_json_writer, "")

        # 构建响应
        data = {
            "md_content": md_content_writer.get_value(),
            "layout": json.loads(content_list_writer.get_value()) if return_layout else None,
            "info": json.loads(middle_json_writer.get_value()) if return_info else None,
            "content_list": json.loads(content_list_writer.get_value()) if return_content_list else None,
            "images": self._get_images(output_image_path) if return_images else None
        }

        # 持久化存储
        if is_json_md_dump:
            self._save_results(output_path, pdf_name, content_list_writer,
                               md_content_writer, middle_json_writer, infer_result)

        # 清理资源
        content_list_writer.close()
        md_content_writer.close()
        middle_json_writer.close()

        return data

    def _get_images(self, image_path):
        """编码图片数据"""
        return {
            os.path.basename(p): f"data:image/jpeg;base64,{b64encode(open(p, 'rb').read()).decode()}"
            for p in glob(f"{image_path}/*.jpg")
        }

    def _save_results(self, output_path, pdf_name, *writers):
        """保存结果文件"""
        writer = FileBasedDataWriter(output_path)
        writer.write_string(f"{pdf_name}_content_list.json", writers[0].get_value())
        writer.write_string(f"{pdf_name}.md", writers[1].get_value())
        writer.write_string(f"{pdf_name}_middle.json", writers[2].get_value())
        writer.write_string(f"{pdf_name}_model.json", json.dumps(writers[3].get_infer_res(), indent=4))

    @staticmethod
    def clean_memory(device=None):
        import gc
        if torch.cuda.is_available():
            if device and device.startswith('cuda'):
                # 提取GPU ID
                gpu_id = int(device.split(':')[-1])
                with torch.cuda.device(gpu_id):
                    torch.cuda.empty_cache()
                    torch.cuda.ipc_collect()
            else:
                # 清理当前设备
                torch.cuda.empty_cache()
                torch.cuda.ipc_collect()
        gc.collect()


if __name__ == '__main__':
    # 添加调试信息
    logger.info("=== LitServer GPU Configuration Debug ===")
    logger.info(f'CUDA_VISIBLE_DEVICES: {os.environ.get("CUDA_VISIBLE_DEVICES", "Not set")}')
    logger.info(f'WORKERS_PER_DEVICE: {os.environ.get("WORKERS_PER_DEVICE", "1")}')
    logger.info(f'Available CUDA devices: {torch.cuda.device_count()}')

    if torch.cuda.is_available():
        for i in range(torch.cuda.device_count()):
            logger.info(f'GPU {i}: {torch.cuda.get_device_name(i)}')
    else:
        logger.warning('CUDA is not available!')

    # 根据容器的环境参数来设置每个GPU的worker数量
    workers_per_device = int(os.environ.get('WORKERS_PER_DEVICE', '1'))
    server_timeout = int(os.environ.get('SERVER_TIMEOUT', False))

    logger.info(f'Starting LitServer with workers_per_device={workers_per_device}')

    # 明确指定设备列表，确保每个GPU上worker数量相等
    if torch.cuda.is_available():
        num_gpus = torch.cuda.device_count()
        # 明确指定每个GPU的ID，而不是使用'auto'
        device_list = list(range(num_gpus))
        logger.info(f'Using explicit device list: {device_list}')

        server = ls.LitServer(
            MinerUAPI(),
            accelerator='cuda',
            devices='auto',  # 明确指定设备列表
            workers_per_device=workers_per_device,
            timeout=server_timeout
        )
    else:
        # CPU fallback
        server = ls.LitServer(
            MinerUAPI(),
            accelerator='cpu',
            workers_per_device=workers_per_device,
            timeout=server_timeout
        )

    server.run(port=8000)
