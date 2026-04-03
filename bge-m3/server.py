"""
BGE-M3 Embedding Server
基于 FlagEmbedding 的全功能嵌入服务，支持稠密/稀疏/ColBERT 向量

接口兼容 OpenAI Embedding API 格式，并扩展了稀疏向量字段
"""
import asyncio
import gc
import os
from typing import List, Optional, Union
from contextlib import asynccontextmanager

import torch
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from FlagEmbedding import BGEM3FlagModel


model: Optional[BGEM3FlagModel] = None
_inference_lock = asyncio.Lock()


class EmbeddingRequest(BaseModel):
    input: Union[str, List[str]]
    model: str = "bge-m3"
    return_dense: bool = True
    return_sparse: bool = True


class SparseVector(BaseModel):
    indices: List[int]
    values: List[float]


class EmbeddingData(BaseModel):
    object: str = "embedding"
    index: int
    embedding: List[float] = Field(default_factory=list)
    sparse_embedding: Optional[SparseVector] = None


class UsageInfo(BaseModel):
    prompt_tokens: int = 0
    total_tokens: int = 0


class EmbeddingResponse(BaseModel):
    object: str = "list"
    data: List[EmbeddingData]
    model: str
    usage: UsageInfo


class HealthResponse(BaseModel):
    status: str
    model: str
    device: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    global model
    model_path = os.getenv("MODEL_PATH", "/models/BAAI/bge-m3")
    device = os.getenv("DEVICE", "cuda" if torch.cuda.is_available() else "cpu")
    use_fp16 = device != "cpu"

    print(f"Loading BGE-M3 from {model_path} on {device} (fp16={use_fp16})")
    model = BGEM3FlagModel(model_path, use_fp16=use_fp16, device=device)
    print("Model loaded successfully")
    yield
    del model


app = FastAPI(title="BGE-M3 Embedding Server", lifespan=lifespan)


@app.get("/health")
async def health():
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    device = os.getenv("DEVICE", "cuda" if torch.cuda.is_available() else "cpu")
    return HealthResponse(status="ok", model="bge-m3", device=device)


@app.post("/v1/embeddings", response_model=EmbeddingResponse)
async def create_embeddings(request: EmbeddingRequest):
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    texts = [request.input] if isinstance(request.input, str) else request.input
    if not texts:
        raise HTTPException(status_code=400, detail="Input must not be empty")

    max_len = int(os.getenv("MAX_LENGTH", "8192"))
    batch_size = int(os.getenv("BATCH_SIZE", "32"))

    async with _inference_lock:
        try:
            with torch.no_grad():
                output = model.encode(
                    texts,
                    batch_size=batch_size,
                    max_length=max_len,
                    return_dense=request.return_dense,
                    return_sparse=request.return_sparse,
                    return_colbert_vecs=False,
                )

            data = []
            for i in range(len(texts)):
                item = EmbeddingData(index=i)

                if request.return_dense and "dense_vecs" in output:
                    vec = output["dense_vecs"][i]
                    item.embedding = vec.tolist() if hasattr(vec, "tolist") else list(vec)

                if request.return_sparse and "lexical_weights" in output:
                    sparse_dict = output["lexical_weights"][i]
                    indices = [int(k) for k in sparse_dict.keys()]
                    values = [float(v) for v in sparse_dict.values()]
                    item.sparse_embedding = SparseVector(indices=indices, values=values)

                data.append(item)
        finally:
            del output
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

    return EmbeddingResponse(
        data=data,
        model=request.model,
        usage=UsageInfo(prompt_tokens=len(texts), total_tokens=len(texts)),
    )


if __name__ == "__main__":
    port = int(os.getenv("PORT", "18085"))
    uvicorn.run(app, host="0.0.0.0", port=port)
