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

from langchain_openai import ChatOpenAI
# from langchain_anthropic import ChatAnthropic  # 【格式三】如需使用 Claude，取消此行注释


# ==============================================================================
# 🔑 API Key 统一配置区（在这里统一填写，下方各代理会引用）
# ==============================================================================
# 【方式一：中转/聚合 API，例如 OpenCode 平台（推荐：一个 Key 调多个不同模型）】
OPENCODE_API_KEY = "YOUR_OPENCODE_KEY"            # 【⬅️ 在这里填入 OpenCode 的 API Key】
OPENCODE_BASE_URL = "https://api.opencode.ai/v1"   # 【⬅️ 填入 OpenCode 提供的 Base URL (注意以 /v1 结尾)】

# 【方式二：官方独立 API Key】
OPENAI_API_KEY = "YOUR_OPENAI_KEY"                 # 【⬅️ 官方 OpenAI Key】
# DEEPSEEK_API_KEY = "YOUR_DEEPSEEK_KEY"           # 【⬅️ 官方 DeepSeek Key】
# ANTHROPIC_API_KEY = "YOUR_ANTHROPIC_KEY"         # 【⬅️ 官方 Claude Key】


# ==============================================================================
# 🤖 各子代理的模型配置（带有自动降级 Fallback 机制）
# ==============================================================================
# 💡 提示：如果使用 OpenCode 等中转站，当主模型调用失败（超时/限流）时，
#          代码会自动无缝切换到 with_fallbacks() 里的备用模型，保证整个状态机稳定运行！

def build_llm(model_name: str, temperature: float = 0.2):
    """辅助函数：快速创建一个模型实例"""
    return ChatOpenAI(
        model=model_name,
        api_key=OPENCODE_API_KEY,      # 这里统一绑定 OpenCode 的 Key
        base_url=OPENCODE_BASE_URL,    # 这里统一绑定 OpenCode 的 Base URL
        temperature=temperature,
    )

# ---- 产品经理 Agent（需要极强的理解力和表达力）----
# 主力用 Claude 3.5，挂了用 GPT-4o，再挂用 DeepSeek
PM_LLM = build_llm("claude-3-5-sonnet", 0.4).with_fallbacks([
    build_llm("gpt-4o", 0.4),
    build_llm("deepseek-chat", 0.4)
])

# ---- 架构师 Agent（需要强逻辑与 API 设计能力）----
# 主力用 GPT-4o，挂了用 Claude 3.5
ARCHITECT_LLM = build_llm("gpt-4o", 0.3).with_fallbacks([
    build_llm("claude-3-5-sonnet", 0.3)
])

# ---- 技术总监 Agent（需要全面审查能力）----
# 主力用 GPT-4o，挂了用 DeepSeek
TECH_LEAD_LLM = build_llm("gpt-4o", 0.2).with_fallbacks([
    build_llm("deepseek-chat", 0.2)
])

# ---- 前端开发 Agent（推荐 DeepSeek 或 Claude）----
FRONTEND_LLM = build_llm("deepseek-chat", 0.2).with_fallbacks([
    build_llm("claude-3-5-sonnet", 0.2)
])

# ---- 后端开发 Agent（推荐 DeepSeek 或 GPT-4o）----
BACKEND_LLM = build_llm("deepseek-chat", 0.2).with_fallbacks([
    build_llm("gpt-4o", 0.2)
])

# ---- QA 测试 Agent（任务较简单，性价比优先）----
QA_LLM = build_llm("gpt-4o-mini", 0.1).with_fallbacks([
    build_llm("deepseek-chat", 0.1)
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
        ],
        "description": "精通现代前端框架与 UI 组件开发",
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
