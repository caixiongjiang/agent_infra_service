#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""=================================================
@PROJECT_NAME: services
@File    : download_model.py
@Author  : caixiongjiang
@Date    : 2025/10/23 15:05
@Function: 
    模型文件下载
@Modify History:
         
@Copyright：Copyright(c) 2024-2026. All Rights Reserved
=================================================="""

# from huggingface_hub import snapshot_download
from modelscope import snapshot_download

if __name__ == "__main__":

    mineru_patterns = [
        "models/Layout/LayoutLMv3/*",
        "models/Layout/YOLO/*",
        "models/MFD/YOLO/*",
        "models/MFR/unimernet_small_2501/*",
        "models/TabRec/TableMaster/*",
        "models/TabRec/StructEqTable/*",
    ]
    model_dir = snapshot_download(
        "opendatalab/PDF-Extract-Kit-1.0",
        allow_patterns=mineru_patterns,
        local_dir="/opt/",
    )

    # layoutreader_pattern = [
    #     "*.json",
    #     "*.safetensors",
    # ]
    # layoutreader_model_dir = snapshot_download(
    #     "hantian/layoutreader",
    #     allow_patterns=layoutreader_pattern,
    #     local_dir="/opt/layoutreader/",
    # )

    print(f"model_dir is: {model_dir}")
    # print(f"layoutreader_model_dir is: {layoutreader_model_dir}")
