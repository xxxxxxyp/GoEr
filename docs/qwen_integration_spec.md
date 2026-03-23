# Qwen LLM 接入规范

## 1. 环境准备
- 在 `.env` 或环境变量中添加：`QWEN_API_KEY=你的阿里灵积平台KEY`
- Base URL: `https://dashscope.aliyuncs.com/compatible-mode/v1`

## 2. 任务逻辑修改 (app/worker/tasks.py)
替换 `llm_summarize` 任务中的 Mock 逻辑：
- **Prompt 策略**: 
  "你是一位资深的机器人与 AI 研究专家。请阅读以下论文摘要，并输出 JSON 格式总结。
   特别注意：如果论文涉及 '3D 建模'、'超声波感知' 或 '语音防伪'，请在核心创新点中重点标注其对实际工程的参考价值。"
- **输出格式约束**: 必须严格符合之前定义的 JSON 结构（core_innovation, methodology, limitations, relevance_score）。

## 3. 给 Agent 的指令
- 请使用 `httpx` 异步或同步调用 Qwen API。
- 实现健壮的 JSON 解析逻辑，防止 LLM 返回非标准格式导致流水线崩溃。
- 如果调用失败，请记录日志并返回基础摘要作为 fallback。