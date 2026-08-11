"""
模型 API 配置 & 子代理能力注册表
================================

本项目支持以下三种主流 API 格式，您只需修改对应代理的配置即可：

【格式一】OpenAI 官方 API（默认）
    ChatOpenAI(model="gpt-4o", api_key="sk-xxxx")

【格式二】OpenAI 兼容格式（DeepSeek / Qwen / 智谱 / 本地 Ollama 等）
    ChatOpenAI(
        model="deepseek-chat",                     # ← 改成对应模型名
        api_key="sk-xxxx",                         # ← 改成对应 Key
        base_url="https://api.deepseek.com/v1"     # ← 改成对应地址
    )

【格式三】Anthropic Claude 系列
    需先安装: pip install langchain-anthropic
    from langchain_anthropic import ChatAnthropic
    ChatAnthropic(model="claude-3-5-sonnet-20241022", api_key="sk-ant-xxxx")
"""

import os

# 必须在导入 langchain_openai 前设置此环境变量，否则 langchain 默认注入的 TCP Keepalive 选项会使系统 HTTP_PROXY 设置失效。
os.environ["LANGCHAIN_OPENAI_TCP_KEEPALIVE"] = "0"

from langchain_openai import ChatOpenAI
# from langchain_anthropic import ChatAnthropic  # 【格式三】如需使用 Claude，取消此行注释


# ==============================================================================
# 🔑 API Key 统一配置区（在这里统一填写，下方各代理会引用）
# ==============================================================================
# 【方式一：中转/聚合 API，例如 OpenCode 平台（推荐：一个 Key 调多个不同模型）】
OPENCODE_API_KEY = ""            # 【⬅️ 请在这里填入你的 API Key，不要提交到 Git】
OPENCODE_BASE_URL = "https://opencode.ai/zen/go/v1"   # 【⬅️ OpenCode Go 官方 Base URL】

# 【方式二：官方独立 API Key】
# OPENAI_API_KEY = "YOUR_OPENAI_KEY"                 # 【⬅️ 官方 OpenAI Key】
# DEEPSEEK_API_KEY = "YOUR_DEEPSEEK_KEY"           # 【⬅️ 官方 DeepSeek Key】
# ANTHROPIC_API_KEY = "YOUR_ANTHROPIC_KEY"         # 【⬅️ 官方 Claude Key】


# ==============================================================================
# 🤖 各子代理的模型配置（带有自动降级 Fallback 机制）
# ==============================================================================
# 💡 提示：这里配置的是适配 OpenCode Go 会员的模型列表。
#          当主模型调用失败（超时/限流）时，会自动无缝切换到备用模型。

import httpx

def build_llm(model_name: str, temperature: float = 0.2):
    """辅助函数：快速创建一个模型实例"""
    # 增加自定义 httpx 客户端，禁用 SSL 验证和 HTTP/2，并且延长超时时间（LLM 生成代码常常需要 30+ 秒）
    custom_client = httpx.Client(verify=False, http2=False, timeout=120.0)
    
    return ChatOpenAI(
        model=model_name,
        api_key=OPENCODE_API_KEY,      # 这里统一绑定 OpenCode 的 Key
        base_url=OPENCODE_BASE_URL,    # 这里统一绑定 OpenCode 的 Base URL
        temperature=temperature,
        http_client=custom_client,
        max_retries=3,                 # 遇到网络抖动自动重试 3 次
        timeout=120,                   # 防止本地提前断开连接
    )

# ---- 产品经理 Agent（需要极强的理解力和表达力）----
# Go 会员推荐主力：Qwen3.8 Max，备用：DeepSeek V4 Pro / GPT 5.6 Luna
PM_LLM = build_llm("qwen3.8-max", 0.4).with_fallbacks([
    build_llm("deepseek-v4-pro", 0.4),
    build_llm("gpt-5.6-luna", 0.4)
])

# ---- 架构师 Agent（需要强逻辑与 API 设计能力）----
# Go 会员推荐主力：DeepSeek V4 Pro，备用：Qwen3.8 Max
ARCHITECT_LLM = build_llm("deepseek-v4-pro", 0.3).with_fallbacks([
    build_llm("qwen3.8-max", 0.3)
])

# ---- 技术总监 Agent（需要全面审查能力）----
# Go 会员推荐主力：Qwen3.8 Max，备用：DeepSeek V4 Pro
TECH_LEAD_LLM = build_llm("qwen3.8-max", 0.2).with_fallbacks([
    build_llm("deepseek-v4-pro", 0.2)
])

# ---- 前端开发 Agent（推荐编程专用模型）----
# Go 会员推荐主力：Kimi K2.7 Code，备用：DeepSeek V4 Pro
FRONTEND_LLM = build_llm("kimi-k2.7-code", 0.1).with_fallbacks([
    build_llm("deepseek-v4-pro", 0.1)
])

# ---- 后端开发 Agent（推荐编程专用模型）----
# Go 会员推荐主力：DeepSeek V4 Pro，备用：Kimi K2.7 Code
BACKEND_LLM = build_llm("deepseek-v4-pro", 0.1).with_fallbacks([
    build_llm("kimi-k2.7-code", 0.1)
])

# ---- QA 测试 Agent（推荐极速便宜的模型进行大量校验）----
# Go 会员推荐主力：DeepSeek V4 Flash，备用：GPT 5.6 Luna
QA_LLM = build_llm("deepseek-v4-flash", 0.1).with_fallbacks([
    build_llm("gpt-5.6-luna", 0.1)
])


# ==============================================================================
# 📋 子代理能力注册表 (Capability Registry)
# ==============================================================================
# 产品经理 Agent 会读取此表，判断现有团队能否覆盖项目所需的全部技术栈。
# 如果您新增了子代理（比如"数据库 Agent"），请在下方注册。
AGENT_REGISTRY = [
    {
        "name": "Frontend Developer",
        "capabilities": [
            "React", "Vue", "HTML", "CSS", "JavaScript", "TypeScript",
            "Tailwind CSS", "响应式布局", "SPA 单页应用",
            "Electron", "Tauri", "桌面应用开发",
        ],
        "description": "精通现代前端框架与 UI 组件开发，支持桌面客户端构建",
    },
    {
        "name": "Backend Developer",
        "capabilities": [
            "Python", "FastAPI", "Flask", "Django", "REST API",
            "数据库设计", "SQL", "SQLite", "PostgreSQL", "用户认证",
        ],
        "description": "精通 Python 后端服务、API 开发与数据库设计",
    },
    # 【如需新增子代理，按照以下格式在此处添加】
    # {
    #     "name": "Database Admin",
    #     "capabilities": ["PostgreSQL", "MongoDB", "Redis", "数据库优化", "数据迁移"],
    #     "description": "精通数据库管理与性能优化",
    # },
]
