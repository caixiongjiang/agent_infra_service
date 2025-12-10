#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""=================================================
@PROJECT_NAME: services
@File    : download_model.py
@Author  : caixiongjiang
@Date    : 2025/12/10 11:56
@Function: 
    下载模型的脚本
@Modify History:
         
@Copyright：Copyright(c) 2024-2026. All Rights Reserved
=================================================="""

#模型下载
from modelscope import snapshot_download

model_dir = snapshot_download('Qwen/Qwen3-Reranker-4B', local_dir="./models/Qwen/Qwen3-Reranker-4B")