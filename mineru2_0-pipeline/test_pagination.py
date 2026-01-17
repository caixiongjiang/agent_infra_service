#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
测试脚本：验证分页功能
演示如何使用 start_page_id 和 end_page_id 参数处理 PDF 的指定页码范围
"""
import requests
import time
from loguru import logger


def test_pagination():
    """测试分页功能"""
    
    API_BASE_URL = "http://localhost:18000"
    test_file = "./demo/pdfs/demo1.pdf"
    
    logger.info("=" * 80)
    logger.info("🧪 测试 MinerU 分页功能")
    logger.info("=" * 80)
    
    # 示例1: 处理前2页（0-1页）
    logger.info("\n示例1: 只处理前2页（page 0-1）")
    with open(test_file, 'rb') as f:
        response = requests.post(
            f'{API_BASE_URL}/api/v1/tasks/submit',
            files={'file': f},
            data={
                'lang': 'ch',
                'start_page_id': 0,
                'end_page_id': 1,  # 处理第0-1页，共2页
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            task_id = result['task_id']
            logger.info(f"✅ 任务已提交: {task_id}")
            logger.info(f"   参数: start_page_id=0, end_page_id=1")
            
            # 等待完成
            wait_for_task(API_BASE_URL, task_id)
        else:
            logger.error(f"❌ 提交失败: {response.text}")
    
    # 示例2: 处理中间页（2-3页）
    logger.info("\n示例2: 只处理中间2页（page 2-3）")
    with open(test_file, 'rb') as f:
        response = requests.post(
            f'{API_BASE_URL}/api/v1/tasks/submit',
            files={'file': f},
            data={
                'lang': 'ch',
                'start_page_id': 2,
                'end_page_id': 3,  # 处理第2-3页，共2页
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            task_id = result['task_id']
            logger.info(f"✅ 任务已提交: {task_id}")
            logger.info(f"   参数: start_page_id=2, end_page_id=3")
            
            # 等待完成
            wait_for_task(API_BASE_URL, task_id)
        else:
            logger.error(f"❌ 提交失败: {response.text}")
    
    # 示例3: 从第3页到最后一页（demo1.pdf 共5页: 0-4）
    logger.info("\n示例3: 从第3页到最后一页（page 3-end）")
    with open(test_file, 'rb') as f:
        response = requests.post(
            f'{API_BASE_URL}/api/v1/tasks/submit',
            files={'file': f},
            data={
                'lang': 'ch',
                'start_page_id': 3,
                # end_page_id 不传或传 None，表示处理到最后一页
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            task_id = result['task_id']
            logger.info(f"✅ 任务已提交: {task_id}")
            logger.info(f"   参数: start_page_id=3, end_page_id=None (到最后一页)")
            
            # 等待完成
            wait_for_task(API_BASE_URL, task_id)
        else:
            logger.error(f"❌ 提交失败: {response.text}")
    
    logger.info("\n" + "=" * 80)
    logger.info("✅ 分页功能测试完成!")
    logger.info("=" * 80)


def wait_for_task(api_url: str, task_id: str, timeout: int = 300):
    """等待任务完成"""
    start_time = time.time()
    
    while True:
        if time.time() - start_time > timeout:
            logger.error(f"⏱️  任务超时: {task_id}")
            return
        
        response = requests.get(f'{api_url}/api/v1/tasks/{task_id}')
        if response.status_code != 200:
            logger.error(f"❌ 查询失败: {response.text}")
            return
        
        result = response.json()
        status = result.get('status')
        
        if status == 'completed':
            logger.info(f"✅ 任务完成: {task_id}")
            logger.info(f"   输出路径: {result.get('result_path')}")
            
            # 获取并显示内容预览
            if result.get('data'):
                content = result['data'].get('content', '')
                logger.info(f"   内容长度: {len(content)} 字符")
                logger.info(f"   内容预览: {content[:100]}...")
            return
        elif status == 'failed':
            logger.error(f"❌ 任务失败: {result.get('error_message')}")
            return
        elif status in ['pending', 'processing']:
            logger.debug(f"⏳ 任务处理中: {status}")
            time.sleep(2)
        else:
            logger.warning(f"⚠️  未知状态: {status}")
            time.sleep(2)


if __name__ == '__main__':
    test_pagination()
