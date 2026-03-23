# FastAPI 核心接口规范 (API Routes & Schemas Spec)

## 1. 概述
本项目后端采用 FastAPI 构建，整体按照 `Router` 模块化组织。所有数据校验和序列化均严格依赖 `Pydantic (v2)` 的 `BaseModel`。
当前为 Phase 1 (MVP) 阶段，核心业务包含：用户鉴权、订阅管理、情报获取。

## 2. 目录结构规范
请在 `app/` 目录下创建/完善以下结构：
- `app/schemas/` (存放 Pydantic 校验模型)
- `app/api/` (存放具体的路由接口)
  - `deps.py` (存放依赖注入函数，如获取数据库 Session、解析 JWT Token 获取当前用户)
  - `endpoints/`
    - `auth.py` (登录注册)
    - `subscriptions.py` (任务订阅)
    - `papers.py` (情报交互)

## 3. 核心 API 路由定义 (Endpoint Specs)

### 3.1 身份认证 (Auth) - `app/api/endpoints/auth.py`
- **POST `/api/v1/auth/register`**
  - **请求体 (UserCreate):** `username`, `email`, `password`
  - **逻辑:** 密码需使用 `passlib` (bcrypt) 加密后存入数据库。
  - **返回 (UserResponse):** 用户基础信息。

- **POST `/api/v1/auth/login/access-token`**
  - **请求体 (OAuth2PasswordRequestForm):** FastAPI 标准表单，包含 `username` 和 `password`。
  - **逻辑:** 验证密码，签发 JWT Token。
  - **返回 (Token):** `{"access_token": "xxx", "token_type": "bearer"}`

### 3.2 订阅管理 (Subscriptions) - `app/api/endpoints/subscriptions.py`
> **注意:** 此路由下的所有接口均需注入 `current_user` 依赖（必须登录）。

- **POST `/api/v1/subscriptions/`**
  - **请求体 (SubscriptionCreate):** ```json
    {
      "source_platform": "arxiv",
      "search_query": "cat:eess.IV AND (ultrasound OR elastography)",
      "cron_schedule": "0 8 * * *"
    }
    ```
  - **逻辑:** 将新订阅任务与当前 user_id 绑定并存入库中。
  - **返回 (SubscriptionResponse):** 完整的订阅记录。

- **GET `/api/v1/subscriptions/`**
  - **逻辑:** 获取当前用户的所有订阅任务列表。

### 3.3 情报流 (Papers & Intelligence) - `app/api/endpoints/papers.py`
> **注意:** 此路由下的所有接口均需注入 `current_user` 依赖。

- **GET `/api/v1/papers/unread`**
  - **逻辑:** 连表查询 `UserPaperInteractions`, `Papers` 和 `PaperSummaries`。过滤出当前用户 `status == 'unread'` 的论文列表。
  - **返回:**
    ```json
    [
      {
        "interaction_id": 1,
        "paper_title": "A Novel Deep Learning Approach for Ultrasound Elastography",
        "authors": ["Author A"],
        "core_innovation": "提出了一种新的 ASVspoof 数据增强算法...",
        "relevance_score": 92.5,
        "added_at": "2026-03-18T20:00:00Z"
      }
    ]
    ```

- **POST `/api/v1/papers/{interaction_id}/read`**
  - **逻辑:** 将指定的交互记录状态更新为 `'read'`。

- **POST `/api/v1/papers/trigger-fetch`**
  - **请求体:** 无
  - **逻辑:** (MVP 预留接口) 遍历当前用户的所有有效订阅，生成后台抓取任务。**目前只需写好接口框架并打印一条日志**，具体的 Celery 队列逻辑我们在下一阶段接入。

## 4. 给 AI 代码 Agent 的生成指令 (Prompt)
1. 请先在 `requirements.txt` 中追加鉴权相关依赖：`passlib[bcrypt]`, `python-jose[cryptography]`, `python-multipart`。
2. 请在 `app/core/security.py` 中实现 JWT 签发和密码 Hash 函数。
3. 请在 `app/schemas/` 下建立对应的 Pydantic Request/Response 模型。
4. 请在 `app/api/endpoints/` 下实现上述 3 个路由文件，并处理好依赖注入（数据库 session 和 OAuth2 当前用户解析）。
5. 最后，请在 `app/main.py` 中使用 `app.include_router()` 将这些路由注册到带有 `/api/v1` 前缀的路由器中。