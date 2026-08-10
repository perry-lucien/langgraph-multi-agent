"""
前端开发 Agent
==============
职责：
1. 严格按照 API 契约编写前端代码
2. 若发现 API 契约在前端无法实现 → 设置 blocker 信号，触发回滚至架构师
3. 若收到 QA 反馈 → 根据真实报错修改代码
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.messages import HumanMessage, SystemMessage
from config import FRONTEND_LLM

FRONTEND_SYSTEM_PROMPT = """你是一位前端开发工程师。你必须严格按照提供的 API 接口契约编写前端代码。

工作规范：
1. 使用 HTML + CSS + JavaScript 编写完整的、可独立运行的前端页面
2. 所有 API 调用必须与契约中定义的接口路径、请求参数、响应格式完全一致
3. 实现基本的错误处理（网络错误、API 返回错误）和加载状态
4. 界面要美观、交互要合理
5. 代码要有清晰的中文注释

⚠️ 关键规则：
- 如果你发现 API 契约中某个接口在前端无法合理实现
  （例如：缺少必要的接口、接口返回的数据格式无法渲染、前后端职责划分不合理），
  你必须在输出的最后一行附加：
  BLOCKER: <无法实现的具体原因和修改建议>
- 如果收到了 QA 的测试反馈，请根据反馈针对性地修正代码
- 输出的代码要完整，不要省略任何部分

请将所有前端代码放在一个 ```html 代码块中（包含内联 CSS 和 JS）。"""


def frontend_agent(state: dict) -> dict:
    """前端开发节点"""
    api_contract = state.get("api_contract", "")
    test_feedback = state.get("test_feedback", "")
    test_result = state.get("test_result", "")

    if test_feedback and test_result == "FAIL":
        print("\n💻 [前端开发 Agent] 收到 QA 反馈，正在修复代码...")
    else:
        print("\n💻 [前端开发 Agent] 正在根据 API 契约编写前端代码...")

    # 构建上下文
    context = f"【API 接口契约】:\n{api_contract}"
    if test_feedback and test_result == "FAIL":
        context += f"\n\n⚠️【QA 测试反馈 - 需要修复】:\n{test_feedback}"

    response = FRONTEND_LLM.invoke([
        SystemMessage(content=FRONTEND_SYSTEM_PROMPT),
        HumanMessage(content=context),
    ])

    code = response.content

    # 检测 BLOCKER 标记
    result = {"frontend_code": code}
    if "BLOCKER:" in code:
        for line in code.split("\n"):
            if "BLOCKER:" in line:
                blocker_msg = line.split("BLOCKER:")[-1].strip()
                result["blocker"] = f"[前端] {blocker_msg}"
                print(f"  🚫 前端遇到死胡同: {blocker_msg}")
                break
    else:
        print("  ✅ 前端代码编写完成")

    return result
