#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""=================================================
@PROJECT_NAME: agent_infra_service
@File    : download_models.py
@Author  : caixiongjiang
@Date    : 2025/12/21 15:28
@Function: 
    MinerU 新版本pipeline模型群组（PDF-Extract-Kit-1.0）
@Modify History:
         
@Copyright：Copyright(c) 2024-2026. All Rights Reserved
=================================================="""

#模型下载
from modelscope import snapshot_download
model_dir = snapshot_download('OpenDataLab/PDF-Extract-Kit-1.0', local_dir='./mineru')