# Celery 异步任务队列规范 (Celery Worker & Tasks Spec)

## 1. 架构目标 (Architecture Intent)
本项目旨在抛弃外部低代码工具 (n8n)，采用 `Celery` + `Redis` 构建高内聚、高鲁棒性的纯代码异步爬虫与情报处理流水线。
当前阶段 (Phase 1 MVP) 需实现从抓取到持久化的 4 步原子任务链 (Task Chain)。

## 2. 基础设施变更 (Infrastructure)
需在 `docker-compose.yml` 中追加 Redis 容器作为 Celery 的 Message Broker:
```yaml
  redis:
    image: redis:7-alpine
    container_name: goer_redis
    restart: always
    ports:
      - "6379:6379"
```

## 3. 目录与模块规范 (Module Structure)
建立 `app/worker/`模块：

`celery_app.py`: Celery 实例配置，需从 `app.core.config` (或类似环境变量) 读取 Redis URL。

`tasks.py`: 存放核心业务流水线。

## 4. 核心流水线定义 (Atomic Task Chain)
请使用 Celery 的 chain (工作流) 将以下 4 个任务串联。所有任务需配置适当的 `@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)` 容错机制。

Task 1: fetch_arxiv_papers(self, search_query: str, max_results: int = 5) -> List[dict]
业务逻辑: 通过 httpx 调用 arXiv API (https://www.google.com/search?q=http://export.arxiv.org/api/query)。

数据处理: 解析 XML，提取 external_id (如 "2403.xxxxx"), title, summary, authors (List), published_date, pdf_url。

输出: 标准化的字典列表。

Task 2: parse_pdf_text(self, papers_list: List[dict]) -> List[dict]
业务逻辑 (MVP): 暂不引入复杂的 PDF 解析库。直接将 Task 1 中的 summary 字段内容视作纯文本，赋值给内部数据流转的新增字段 full_text。

Task 3: llm_summarize(self, papers_list: List[dict]) -> List[dict]
业务逻辑: 遍历列表，针对每篇的 full_text 调用外部 LLM。MVP 阶段请先实现一个 Mock 函数，模拟返回如下结构的 JSON：

core_innovation: str (一句话总结)

methodology: str

limitations: str

relevance_score: float (0-100)

输出: 将结构化总结数据合并入原字典列表。

Task 4: save_to_database(self, papers_list: List[dict], user_id: int, subscription_id: int)
业务逻辑: 将清洗并总结后的数据持久化到 PostgreSQL。

Papers 表: 依据 external_id 进行 Upsert 或 Ignore 插入。

PaperSummaries 表: 插入对应的 AI 总结。

UserPaperInteractions 表: 生成当前 user_id 与对应 paper_id 的关联记录，status 设为 'unread'。

## 5. 给 GPT-5.3-Codex 的专属开发指令 (Agent Prompt)
作为资深 Python 架构师，请严格依据上述规范实现 Celery 模块。请特别注意以下工程挑战：

依赖管理: 请在 requirements.txt 中补充 celery, redis, httpx。

异步与同步的桥接 (CRITICAL): 我们的 SQLAlchemy 引擎 (asyncpg) 是纯异步的，而 Celery worker 默认在同步线程中运行。在 Task 4 中操作数据库时，你必须使用 asyncio.run() 或创建独立的 Event Loop 来安全地调用我们的 AsyncSession，严防 RuntimeError: asyncio.run() cannot be called from a running event loop 或协程未等待的错误。

API 触发点: 请在 app/api/endpoints/papers.py 的 /trigger-fetch 接口中，将之前的伪代码替换为实际的 Celery Chain 调用 (fetch_arxiv_papers.s(...) | parse_pdf_text.s() | ...).apply_async()。

日志与类型: 保持严格的 Type Hints (使用 typing 模块) 和标准 logging。