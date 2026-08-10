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
OPENAI_API_KEY = "YOUR_API_KEY"        # 【⬅️ 在这里填入您的 OpenAI API Key】
# DEEPSEEK_API_KEY = "YOUR_API_KEY"    # 【⬅️ 如使用 DeepSeek，在这里填入】
# ANTHROPIC_API_KEY = "YOUR_API_KEY"   # 【⬅️ 如使用 Claude，在这里填入】


# ==============================================================================
# 🤖 各子代理的模型配置（每个代理可独立配置不同的模型和 API）
# ==============================================================================

# ---- 产品经理 Agent（需要极强的理解力和表达力）----
PM_LLM = ChatOpenAI(
    model="gpt-4o",                  # 【⬅️ 修改模型名称】
    api_key=OPENAI_API_KEY,          # 【⬅️ 修改 API Key 变量名】
    # base_url="https://api.deepseek.com/v1",  # 【格式二】取消注释并修改为目标 API 地址
    temperature=0.4,
)
# PM_LLM = ChatAnthropic(model="claude-3-5-sonnet-20241022", api_key=ANTHROPIC_API_KEY)  # 【格式三】

# ---- 架构师 Agent（需要强逻辑与 API 设计能力）----
ARCHITECT_LLM = ChatOpenAI(
    model="gpt-4o",                  # 【⬅️ 修改模型名称】
    api_key=OPENAI_API_KEY,          # 【⬅️ 修改 API Key 变量名】
    # base_url="...",                # 【格式二】取消注释并修改
    temperature=0.3,
)

# ---- 技术总监 Agent（需要全面审查能力）----
TECH_LEAD_LLM = ChatOpenAI(
    model="gpt-4o",                  # 【⬅️ 修改模型名称】
    api_key=OPENAI_API_KEY,          # 【⬅️ 修改 API Key 变量名】
    # base_url="...",                # 【格式二】取消注释并修改
    temperature=0.2,
)

# ---- 前端开发 Agent（需要代码生成能力）----
FRONTEND_LLM = ChatOpenAI(
    model="gpt-4o-mini",             # 【⬅️ 可替换为 deepseek-coder 等代码专用模型以节省成本】
    api_key=OPENAI_API_KEY,          # 【⬅️ 修改 API Key 变量名】
    # base_url="...",                # 【格式二】取消注释并修改
    temperature=0.2,
)

# ---- 后端开发 Agent（需要代码生成能力）----
BACKEND_LLM = ChatOpenAI(
    model="gpt-4o-mini",             # 【⬅️ 可替换为 deepseek-coder 等代码专用模型以节省成本】
    api_key=OPENAI_API_KEY,          # 【⬅️ 修改 API Key 变量名】
    # base_url="...",                # 【格式二】取消注释并修改
    temperature=0.2,
)

# ---- QA 测试 Agent（任务相对简单，可用小模型节省成本）----
QA_LLM = ChatOpenAI(
    model="gpt-4o-mini",             # 【⬅️ 修改模型名称】
    api_key=OPENAI_API_KEY,          # 【⬅️ 修改 API Key 变量名】
    # base_url="...",                # 【格式二】取消注释并修改
    temperature=0.1,
)


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
