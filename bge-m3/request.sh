#!/bin/bash

echo "=== 1. 健康检查 ==="
curl -s http://localhost:18085/health | python3 -m json.tool
echo ""

echo "=== 2. 获取稠密 + 稀疏向量 (默认) ==="
curl -s http://localhost:18085/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{
    "input": "什么是Agent基础设施服务？",
    "model": "bge-m3",
    "return_dense": true,
    "return_sparse": true
  }' | python3 -m json.tool
echo ""

echo "=== 3. 仅获取稠密向量 ==="
curl -s http://localhost:18085/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{
    "input": "什么是Agent基础设施服务？",
    "model": "bge-m3",
    "return_dense": true,
    "return_sparse": false
  }' | python3 -m json.tool
echo ""

echo "=== 4. 批量请求 ==="
curl -s http://localhost:18085/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{
    "input": ["第一段文本", "第二段文本", "第三段文本"],
    "model": "bge-m3",
    "return_dense": true,
    "return_sparse": true
  }' | python3 -m json.tool
