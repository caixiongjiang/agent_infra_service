#!/bin/bash

curl -X POST https://localhost:18083/v1/rerank \
    -H "Authorization: Bearer caixj-test" \
    -H "Content-Type: application/json" \
    -d '{
        "model": "qwen3-reranker-0.6b",
        "query": "苹果怎么吃？",
        "documents": [
            "苹果可以直接洗净生吃。",
            "苹果公司发布了新手机。",
            "做成苹果派也很美味。"
        ],
        "top_n": 2
    }'