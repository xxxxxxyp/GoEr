import os


class Settings:
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    arxiv_api_url: str = os.getenv("ARXIV_API_URL", "http://export.arxiv.org/api/query")
    qwen_api_key: str = os.getenv("QWEN_API_KEY", "sk-8b7c5cc82ba840259885d715d9cf9ad0")
    qwen_base_url: str = os.getenv(
        "QWEN_BASE_URL",
        "https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    qwen_model: str = os.getenv("QWEN_MODEL", "qwen-plus")
    qwen_timeout_seconds: float = float(os.getenv("QWEN_TIMEOUT_SECONDS", "45"))


settings = Settings()
