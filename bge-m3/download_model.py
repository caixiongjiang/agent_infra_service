#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from modelscope import snapshot_download
import os

local_dir = "./models/BAAI/bge-m3"
os.makedirs(local_dir, exist_ok=True)

model_dir = snapshot_download('BAAI/bge-m3', local_dir=local_dir)
print(f"Model downloaded to {model_dir}")
