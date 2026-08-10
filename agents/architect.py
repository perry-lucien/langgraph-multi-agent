"""
架构师 Agent
============
职责：
1. 接收 PRD，设计严谨的前后端 API 接口契约
2. 若被技术总监打回 → 根据审查反馈修改契约
3. 若被开发打回（BLOCKER）→ 根据开发反馈修改契约
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.messages import HumanMessage, SystemMessage
from config import ARCHITECT_LLM

ARCHITECT_SYSTEM_PROMPT = """你是一位资深软件架构师。你的职责是根据 PRD（产品需求文档）设计清晰严谨的前后端 API 接口契约。

你的输出必须包含以下内容：

1. 【技术架构概述】简述前后端技术选型与整体架构
2. 【数据模型】核心数据结构 / 数据库表设计（含字段、类型、约束）
3. 【API 接口列表】每个接口必须包含：
   - 请求方法与路径（例如 GET /api/todos）
   - 请求参数（Query / Body，含类型与是否必填）
   - 响应格式（JSON Schema，含成功与失败示例）
   - 错误码定义
4. 【前后端职责划分】明确哪些逻辑在前端处理，哪些在后端处理

⚠️ 重要原则：
- 接口设计要考虑可实现性，不要设计超出团队能力的复杂方案
- 所有接口的命名规范和参数风格必须前后统一
- 充分考虑错误处理、空数据、分页等边界情况
- 保持简洁：能用一个接口解决的，不要拆成两个"""


def architect_agent(state: dict) -> dict:
    """架构师节点"""
    prd = state.get("prd", "")
    review_feedback = state.get("review_feedback", "")
    blocker = state.get("blocker", "")

    # 根据触发来源构建不同的上下文
    context_parts = [f"【PRD 产品需求文档】:\n{prd}"]

    if blocker:
        print("\n🔧 [架构师 Agent] 收到开发团队的 BLOCKER 反馈，正在修改 API 契约...")
        context_parts.append(
            f"\n\n⚠️【开发团队反馈 - BLOCKER 死胡同】:\n{blocker}\n"
            f"请根据此反馈修改你的 API 契约设计，解决开发团队遇到的技术障碍。"
        )
    elif review_feedback:
        print("\n🔧 [架构师 Agent] 收到技术总监的修改建议，正在修改 API 契约...")
        context_parts.append(
            f"\n\n⚠️【技术总监审查反馈 - 需修改】:\n{review_feedback}\n"
            f"请根据此反馈修改你的 API 契约设计。"
        )
    else:
        print("\n🏗️ [架构师 Agent] 正在根据 PRD 设计 API 接口契约...")

    response = ARCHITECT_LLM.invoke([
        SystemMessage(content=ARCHITECT_SYSTEM_PROMPT),
        HumanMessage(content="\n".join(context_parts)),
    ])

    # 清除旧的 blocker 和 review 状态（防止下一轮误判）
    return {
        "api_contract": response.content,
        "blocker": "",            # 清除死胡同标记
        "review_feedback": "",    # 清除旧的审查反馈
        "review_status": "",      # 重置审批状态
    }
