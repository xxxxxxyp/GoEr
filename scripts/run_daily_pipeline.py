import asyncio
import logging
import sys
import os

# 将项目根目录加入环境变量，方便导入 app 模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.subscription import Subscription

# 导入你原有的工作流核心函数（我们将传入 None 来绕过 Celery 的 self 绑定）
from app.worker.tasks import (
    fetch_arxiv_papers,
    parse_pdf_text,
    llm_summarize,
    _save_to_database_async
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    logger.info("🚀 启动 GoEr Serverless 批处理流水线...")

    async with AsyncSessionLocal() as db:
        # 1. 查找所有激活的订阅
        result = await db.execute(select(Subscription).where(Subscription.is_active == True))
        subscriptions = result.scalars().all()

        if not subscriptions:
            logger.warning("⚠️ 没有找到激活的订阅规则。")
            return

        for sub in subscriptions:
            logger.info(f"🔍 正在执行订阅规则 (ID: {sub.id}, 关键词: {sub.search_query})")

            try:
                # 2. 抓取论文 (Celery 会自动处理 self，直接传参数即可)
                papers = fetch_arxiv_papers(search_query=sub.search_query, max_results=3)
                logger.info(f"📥 抓取到 {len(papers)} 篇论文。")

                if not papers:
                    continue

                # 3. 解析文本
                parsed_papers = parse_pdf_text(papers_list=papers)

                # 4. 调用通义千问 API 进行深度提取
                logger.info("🧠 正在调用 Qwen 进行总结...")
                summarized_papers = llm_summarize(papers_list=parsed_papers)

                # 5. 存入 Supabase 数据库
                logger.info("💾 正在将数据持久化到 Supabase...")
                stats = await _save_to_database_async(
                    papers_list=summarized_papers,
                    user_id=sub.user_id,
                    subscription_id=sub.id
                )
                logger.info(f"✅ 入库成功: 新增论文 {stats['inserted_papers']} 篇, 生成总结 {stats['upserted_summaries']} 条。")

            except Exception as e:
                logger.error(f"❌ 处理订阅 {sub.id} 时出错: {e}")

    logger.info("🎉 所有任务执行完毕！")

if __name__ == "__main__":
    # Windows 环境下防止 asyncpg 报错
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())