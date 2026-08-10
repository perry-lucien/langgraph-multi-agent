"""
后端开发 Agent
==============
职责：
1. 严格按照 API 契约编写后端代码
2. 若发现 API 契约在后端无法实现 → 设置 blocker 信号，触发回滚至架构师
3. 若收到 QA 反馈 → 根据真实报错修改代码
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.messages import HumanMessage, SystemMessage
from config import BACKEND_LLM

BACKEND_SYSTEM_PROMPT = """你是一位后端开发工程师。你必须严格按照提供的 API 接口契约编写后端代码。

工作规范：
1. 使用 Python + FastAPI 编写后端服务
2. 所有 API 路径、请求方法、请求参数、响应格式必须与契约完全一致
3. 使用 SQLite 实现数据持久化（使用 SQLAlchemy 或直接用 sqlite3）
4. 实现完善的错误处理和数据验证（使用 Pydantic 模型）
5. 包含 CORS 中间件配置（允许前端跨域调用）
6. 代码要有清晰的中文注释

⚠️ 关键规则：
- 如果你发现 API 契约中某个接口在后端无法合理实现
  （例如：需要外部服务但未说明配置、数据库关系设计不合理、接口逻辑存在矛盾），
  你必须在输出的最后一行附加：
  BLOCKER: <无法实现的具体原因和修改建议>
- 如果收到了 QA 的测试反馈，请根据反馈针对性地修正代码
- 输出的代码要完整，不要省略任何部分

请将后端代码放在 ```python 代码块中。如有多个文件，用注释 # === 文件名 === 分隔。"""


def backend_agent(state: dict) -> dict:
    """后端开发节点"""
    api_contract = state.get("api_contract", "")
    test_feedback = state.get("test_feedback", "")
    test_result = state.get("test_result", "")

    if test_feedback and test_result == "FAIL":
        print("\n🔌 [后端开发 Agent] 收到 QA 反馈，正在修复代码...")
    else:
        print("\n🔌 [后端开发 Agent] 正在根据 API 契约编写后端代码...")

    # 构建上下文
    context = f"【API 接口契约】:\n{api_contract}"
    if test_feedback and test_result == "FAIL":
        context += f"\n\n⚠️【QA 测试反馈 - 需要修复】:\n{test_feedback}"

    response = BACKEND_LLM.invoke([
        SystemMessage(content=BACKEND_SYSTEM_PROMPT),
        HumanMessage(content=context),
    ])

    code = response.content

    # 检测 BLOCKER 标记
    result = {"backend_code": code}
    if "BLOCKER:" in code:
        for line in code.split("\n"):
            if "BLOCKER:" in line:
                blocker_msg = line.split("BLOCKER:")[-1].strip()
                # 如果已有前端的 blocker，拼接上（并发场景下两者可能同时触发）
                existing = state.get("blocker", "")
                if existing:
                    result["blocker"] = f"{existing}\n[后端] {blocker_msg}"
                else:
                    result["blocker"] = f"[后端] {blocker_msg}"
                print(f"  🚫 后端遇到死胡同: {blocker_msg}")
                break
    else:
        print("  ✅ 后端代码编写完成")

    return result
