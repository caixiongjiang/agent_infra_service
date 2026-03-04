#!/bin/bash

curl http://localhost:18084/v1/embeddings \
  -H "Authorization: Bearer caixj-test" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3-embedding-0.6b",
    "input": [
      "这是第一条文本：我想查询深度学习的资料",
      "这是第二条文本：Qwen3-Embedding 的效果怎么样？",
      "这是第三条文本：批量发送可以减少网络开销并提高吞吐量"
    ]
  }'