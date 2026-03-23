from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import api_router

app = FastAPI(title="GoEr API")

# 配置 CORS 跨域允许
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 现阶段为了方便调试，允许所有域名访问；以后商业化了可以改成指定的 Vercel 域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}