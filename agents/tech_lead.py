"""
技术总监 Agent（架构 QA / 红蓝对抗）
====================================
职责：
1. 以"挑刺"视角严格审查架构师输出的 API 契约
2. 检查接口完整性、安全性、一致性、可实现性
3. 输出 APPROVED（通过）或 REJECTED（打回并附修改建议）
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.messages import HumanMessage, SystemMessage
from config import TECH_LEAD_LLM

TECH_LEAD_SYSTEM_PROMPT = """你是一位严苛的技术总监 (Tech Lead)，负责审查架构师提交的 API 接口契约。

你的审查标准（按重要性排列）：
1. 【完整性】PRD 中提到的每个功能，是否都有对应的 API 接口支撑？
2. 【一致性】接口命名、参数风格是否统一？前后端数据格式是否匹配？
3. 【安全性】是否考虑了身份验证？是否有敏感数据暴露风险？
4. 【可实现性】接口设计是否过于复杂？开发团队是否能在合理时间内实现？
5. 【健壮性】是否考虑了错误处理、分页、空数据、并发等边界情况？

审查规则：
- 如果没有严重问题（仅有小瑕疵可以放过），请回复的第一行为: APPROVED
- 如果存在必须修改的重大问题，请回复的第一行为: REJECTED
  并逐一列出问题编号、问题描述、和具体修改建议
- 你的回复第一行必须且仅为 APPROVED 或 REJECTED 二选一"""


def tech_lead_agent(state: dict) -> dict:
    """技术总监节点"""
    review_rounds = state.get("review_rounds", 0)
    print(f"\n🔍 [技术总监 Agent] 正在审查 API 契约（第 {review_rounds + 1} 轮）...")

    api_contract = state.get("api_contract", "")
    prd = state.get("prd", "")

    response = TECH_LEAD_LLM.invoke([
        SystemMessage(content=TECH_LEAD_SYSTEM_PROMPT),
        HumanMessage(content=(
            f"【原始 PRD 产品需求文档】:\n{prd}\n\n"
            f"【架构师提交的 API 契约】:\n{api_contract}"
        )),
    ])

    result_text = response.content.strip()
    is_approved = result_text.upper().startswith("APPROVED")

    if is_approved:
        print("  ✅ 技术总监审批通过！API 契约质量合格。")
    else:
        print(f"  ❌ 技术总监打回修改（第 {review_rounds + 1} 轮）")

    return {
        "review_status": "APPROVED" if is_approved else "REJECTED",
        "review_feedback": "" if is_approved else result_text,
        "review_rounds": review_rounds + 1,
    }
