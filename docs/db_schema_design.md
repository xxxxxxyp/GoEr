# 数据库实体关系设计规范 (Database Schema Design Spec)

## 1. 概述
本项目采用双擎数据库架构：
- **PostgreSQL (关系型数据库)**：负责存储用户系统、论文元数据、结构化总结以及任务状态。
- **Qdrant / Milvus (向量数据库)**：负责存储经本地 Embedding 模型（如 BGE-M3）处理后的文本向量，支持后续的高级 RAG 检索。

## 2. PostgreSQL 核心表结构 (ER 关系)

### 2.1 Users (用户表)
存储多租户环境下的系统用户信息。
- `id` (Integer, Primary Key, Auto Increment)
- `username` (String 50, Unique, Not Null)
- `email` (String 100, Unique, Not Null)
- `hashed_password` (String 255, Not Null)
- `is_active` (Boolean, Default: True)
- `created_at` (DateTime, Default: func.now())

### 2.2 Subscriptions (用户订阅任务表)
记录用户关注的特定研究领域和爬虫抓取关键词（如针对“ASVspoof 数据增强”、“医学图像分割”或“超声波阵列”的定制化追踪）。
- `id` (Integer, Primary Key)
- `user_id` (Integer, ForeignKey('users.id', ondelete="CASCADE"))
- `source_platform` (String 50) - 枚举值：'arxiv', 'ieee', 'medrxiv' 等
- `search_query` (String 255) - 例如："cat:eess.IV AND (ultrasound OR elastography)"
- `cron_schedule` (String 50) - 调度频率，例如 "0 8 * * *" (每天早8点)
- `is_active` (Boolean, Default: True)

### 2.3 Papers (论文元数据表)
系统的核心资源库。为了避免重复抓取，需要根据外部 ID 设置唯一约束。
- `id` (Integer, Primary Key)
- `external_id` (String 100, Unique, Index) - 例如 arXiv 的 "2403.xxxxx"
- `title` (String 500, Not Null)
- `authors` (JSONB) - 作者列表，例如 `["Author A", "Author B"]`
- `abstract_original` (Text) - 平台原始摘要
- `published_date` (Date)
- `pdf_url` (String 500)
- `is_parsed` (Boolean, Default: False) - PDF 纯文本是否已成功清洗
- `created_at` (DateTime, Default: func.now())

### 2.4 PaperSummaries (AI 结构化总结表)
存储经过云端大模型提纯后的核心高价值情报。与 `Papers` 表为 1 对 1 关系。
- `id` (Integer, Primary Key)
- `paper_id` (Integer, ForeignKey('papers.id', ondelete="CASCADE"), Unique)
- `core_innovation` (Text) - 核心创新点（一句话总结）
- `methodology` (Text) - 具体方法论与实验设计
- `limitations` (Text) - 研究局限性与未来方向
- `relevance_score` (Float) - AI 判定的重要性评分 (0-100)
- `llm_model` (String 50) - 例如 "deepseek-chat", "kimi"
- `updated_at` (DateTime, onupdate: func.now())

### 2.5 UserPaperInteractions (用户情报交互映射表)
多租户核心逻辑。同一篇论文可能被多个用户的不同关键词命中，需记录各自的阅读状态。
- `id` (Integer, Primary Key)
- `user_id` (Integer, ForeignKey('users.id', ondelete="CASCADE"))
- `paper_id` (Integer, ForeignKey('papers.id', ondelete="CASCADE"))
- `subscription_id` (Integer, ForeignKey('subscriptions.id', ondelete="SET NULL"), Nullable) - 是哪个订阅任务抓到这篇的
- `status` (String 20, Default: "unread") - 状态：'unread' (未读), 'read' (已读), 'starred' (星标重点)
- `added_at` (DateTime, Default: func.now())
- **Constraint**: UniqueConstraint('user_id', 'paper_id')

---

## 3. 向量数据库 (Qdrant) 集合设计

在 MVP 阶段，向量数据库主要用于存储长文本切片。

### Collection Name: `paper_knowledge_base`
- **Vector Dimension**: 1024 (假设本地使用 BGE-M3 模型，需根据实际模型动态调整)
- **Distance Metric**: Cosine (余弦相似度)

### Payload (元数据设计)
每次将论文文本切块（Chunk）并向量化存入时，必须携带以下 Payload，以便后续进行精确的混合过滤（Hybrid Search）：
```json
{
  "paper_id": 1024,                  // 对应 PostgreSQL 中的 papers.id
  "chunk_index": 3,                  // 该段落在原论文中的顺序
  "chunk_text": "We constructed a 3-transmitter 4-receiver ultrasonic array...", // 原始文本段落
  "authors": ["Author A"],           // 冗余存储，加速基于作者的过滤
  "published_year": 2026             // 冗余存储，加速时间窗口过滤
}