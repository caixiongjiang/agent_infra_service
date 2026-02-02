# Agent 基础设施服务集合

> 使用 Docker 快速构建 Agent 应用所需的各类基础设施服务

## 📋 项目概述

本项目提供了一套完整的容器化基础设施服务，专为 AI Agent 应用设计。所有服务均基于 Docker 部署，开箱即用，支持快速搭建开发和生产环境。

## 🗂️ 服务目录

### 📊 数据存储服务

| 服务 | 说明 | 目录 | 端口 |
|------|------|------|------|
| **MongoDB** | NoSQL 文档数据库 | [`mongodb/`](./mongodb/) | 27017 |
| **MySQL** | 关系型数据库 (v8) | [`mysql/`](./mysql/) | 3306 |
| **PostgreSQL** | 高级关系型数据库 | [`pgsql/`](./pgsql/) | 5432 |
| **Neo4j** | 图数据库 | [`neo4j/`](./neo4j/) | 7474, 7687 |
| **Redis** | 内存缓存数据库 | [`redis/`](./redis/) | 6379 |
| **Milvus** | 向量数据库 (支持 CPU/GPU) | [`milvus/`](./milvus/) | 19530, 3000 |

### 🔄 消息队列服务

| 服务 | 说明 | 目录 | 端口 |
|------|------|------|------|
| **Kafka** | 分布式消息队列 | [`kafka/`](./kafka/) | 9092 |

### 🤖 AI 能力服务

| 服务 | 说明 | 目录 | 端口 |
|------|------|------|------|
| **Embedding** | 向量嵌入服务 (基于 vLLM) | [`embedding/`](./embedding/) | 自定义 |
| **Reranker** | 重排序服务 (基于 vLLM) | [`reranker/`](./reranker/) | 自定义 |

### 📄 文档处理服务

| 服务 | 说明 | 目录 | 端口 |
|------|------|------|------|
| **MinerU Pipeline** | MinerU 文档解析服务 (v1) | [`mineru-pipeline/`](./mineru-pipeline/) | 自定义 |
| **MinerU 天枢** | 企业级多 GPU 文档解析服务 (v2.0) | [`mineru2_0-pipeline/`](./mineru2_0-pipeline/) | 8000, 9000 |

> 💡 **推荐**: 新项目建议使用 [MinerU 天枢](./mineru2_0-pipeline/)，它提供了更强大的企业级功能、更好的性能和完整的 RESTful API。

## 🚀 快速开始

每个服务目录都包含独立的配置文件和启动脚本：

```bash
# 进入服务目录
cd <service-directory>

# 启动服务
./start_service.sh

# 停止服务
./stop_service.sh
```

### 配置文件说明

- `docker-compose-*.yml` - Docker Compose 配置文件
- `*.env` - 环境变量配置文件
- `start_service.sh` - 服务启动脚本
- `stop_service.sh` - 服务停止脚本

## 🔧 环境要求

### 基础要求
- Docker 20.10+
- Docker Compose 2.0+

### GPU 服务要求（可选）
以下服务支持 GPU 加速（可选，非必需）：
- Embedding (vLLM) - 需要 GPU
- Reranker (vLLM) - 需要 GPU
- MinerU Pipeline - 需要 GPU
- MinerU 天枢 - 需要 GPU
- Milvus - 可选 GPU 加速（提供 CPU/GPU 两种部署方式）

**GPU 环境配置：**
- NVIDIA Driver 525+
- CUDA 12.1+
- NVIDIA Container Toolkit

## 📚 详细文档

### 数据存储服务

#### MongoDB
- **用途**: 存储非结构化/半结构化数据、文档存储
- **典型场景**: Agent 对话历史、知识库文档、配置信息

#### MySQL
- **用途**: 存储结构化关系数据
- **典型场景**: 用户信息、业务数据、事务处理

#### PostgreSQL
- **用途**: 高级关系型数据存储，支持 JSON、向量扩展
- **典型场景**: 复杂查询、向量检索（配合 pgvector）

#### Neo4j
- **用途**: 图数据存储和查询
- **典型场景**: 知识图谱、实体关系、推理链路
- **特性**: 预配置 APOC 插件

#### Redis
- **用途**: 高性能缓存、会话存储
- **典型场景**: API 限流、会话管理、临时数据缓存

#### Milvus
- **用途**: 专业向量数据库，高性能向量检索
- **典型场景**: RAG 向量检索、语义搜索、相似度匹配、多模态检索
- **特性**: 
  - 支持 CPU 和 GPU 两种部署模式
  - 内置 Attu Web 管理界面（端口 3000）
  - 支持多种索引类型（FLAT、IVF、HNSW 等）
  - 毫秒级检索响应
  - 支持标量过滤和混合查询

### 消息队列服务

#### Kafka
- **用途**: 分布式消息队列、事件流处理
- **典型场景**: Agent 间通信、异步任务处理、事件溯源

### AI 能力服务

#### Embedding
- **用途**: 文本向量化服务
- **技术栈**: vLLM 推理引擎
- **典型场景**: RAG 检索、语义搜索、相似度计算

#### Reranker
- **用途**: 检索结果重排序
- **技术栈**: vLLM 推理引擎
- **典型场景**: 提升检索精度、优化召回结果

### 文档处理服务

#### MinerU 天枢 (推荐)
- **用途**: 企业级文档解析服务
- **核心特性**:
  - ✅ 多 GPU 负载均衡
  - ✅ 异步任务队列（SQLite）
  - ✅ RESTful API
  - ✅ 支持 PDF、图片、Office、HTML 等多种格式
  - ✅ Worker 主动拉取模式，0.5秒响应速度
  - ✅ 智能双解析器（MinerU + MarkItDown）
- **详细文档**: [点击查看](./mineru2_0-pipeline/README.md)

#### MinerU Pipeline (Legacy)
- **用途**: 基础文档解析服务
- **状态**: 维护模式，建议迁移到天枢版本

## 🛠️ 服务组合建议

### 最小 RAG 系统
```
Milvus + Embedding + MinerU 天枢
```

### 完整 Agent 系统
```
Milvus + Redis + Kafka + Embedding + Reranker + MinerU 天枢
```

### 知识图谱系统
```
Neo4j + MongoDB + Embedding + MinerU 天枢
```

## 📝 注意事项

1. **端口冲突**: 启动服务前请确保相关端口未被占用
2. **资源配置**: 根据实际需求调整 `.env` 文件中的资源配置
3. **数据持久化**: 所有服务默认配置了数据卷持久化
4. **GPU 服务**: AI 服务需要先下载模型文件（执行各目录下的 `download_model.py`）
5. **网络配置**: 服务间通信需要在同一 Docker 网络中，或通过 host 网络模式

## 🔐 安全建议

- 生产环境请修改默认密码（在各服务的 `.env` 文件中）
- 建议配置防火墙规则，限制服务访问范围
- Neo4j 等服务建议启用 SSL/TLS
- 敏感信息不要提交到版本控制系统

## 📄 许可证

本项目遵循 [LICENSE](./LICENSE) 协议

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📮 联系方式

如有问题或建议，请通过 Issue 反馈。

---

**Agent 基础设施服务** - 一站式容器化基础设施解决方案 🚀
