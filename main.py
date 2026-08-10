"""
终极多 Agent 状态机 - 主入口
============================
基于 LangGraph 编排的企业级多 Agent 工作流系统。

系统工作流:
  用户需求 → PM(需求+策划+经验查阅) → [人工确认 PRD]
  → 架构师(API契约) ⇄ 技术总监(红蓝对抗审查)
  → [并行] 前端开发 + 后端开发 → [汇合检查 BLOCKER]
  → QA 沙盒测试 → 交付 / 打回重试
  → 经验沉淀至本地数据库

防护机制:
  - 能力缺失挂起（PM 检测）
  - 架构对抗熔断（≥3 轮强制人工介入）
  - 开发死胡同回滚（BLOCKER → 架构师）
  - 测试重试熔断（≥3 次强制放行）
  - 沙盒执行超时（30 秒强制终止）
  - 断电崩溃恢复（Checkpoint 断点续传）
"""

import sys
import os

# 确保项目根目录在 Python 路径中
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from state import AgentState
from config import AGENT_REGISTRY
from agents.pm import pm_agent
from agents.architect import architect_agent
from agents.tech_lead import tech_lead_agent
from agents.frontend import frontend_agent
from agents.backend import backend_agent
from agents.qa import qa_agent
from memory.experience_db import ExperienceDB

experience_db = ExperienceDB()


# ==============================================================================
# 路由函数 (Router Functions) —— 母代理的"决策大脑"
# ==============================================================================

def pm_router(state: dict) -> str:
    """
    PM 完成后的路由：
    - 发现能力缺口 → 终止并提示人工介入
    - 能力匹配 → 进入架构设计阶段
    """
    if state.get("missing_capability"):
        print(f"\n🛑 [系统挂起] 能力缺口: {state['missing_capability']}")
        print("  请在 config.py 的 AGENT_REGISTRY 中补充对应能力后重新运行。")
        return "human_intervention"
    return "architect"


def review_router(state: dict) -> str:
    """
    技术总监审查后的路由：
    - APPROVED → 进入并行开发（通过 dispatch 分发节点）
    - REJECTED 且轮数 < 3 → 打回架构师修改
    - REJECTED 且轮数 ≥ 3 → 熔断，请求人工介入
    """
    if state.get("review_status") == "APPROVED":
        return "dispatch"
    elif state.get("review_rounds", 0) >= 3:
        print("\n🛑 [熔断] 架构师与技术总监对抗已超过 3 轮，请人工介入审查 API 契约。")
        return "human_intervention"
    else:
        return "architect"


def dev_check_router(state: dict) -> str:
    """
    开发完成后的汇合检查（Fan-in 之后）：
    - 任一开发遇到 BLOCKER → 回滚至架构师修改契约
    - 无 BLOCKER → 进入 QA 测试
    """
    if state.get("blocker"):
        print(f"\n🔄 [回滚] 开发遇到死胡同，回滚至架构师修改契约:")
        print(f"  {state['blocker']}")
        return "architect"
    return "qa"


def qa_router(state: dict) -> str:
    """
    QA 测试后的路由：
    - PASS → 经验沉淀 → 结束
    - FAIL 且重试 < 3 → 打回开发重做（通过 dispatch 并行分发）
    - FAIL 且重试 ≥ 3 → 熔断（QA Agent 内部已强制 PASS）
    """
    if state.get("test_result") == "PASS":
        return "save_experience"
    elif state.get("dev_revision_count", 0) >= 3:
        print("\n🛑 [熔断] 开发-测试循环已超过 3 次，请人工介入。")
        return "human_intervention"
    else:
        return "dispatch"


# ==============================================================================
# 辅助节点 (Helper Nodes)
# ==============================================================================

def dispatch_node(state: dict) -> dict:
    """
    并行分发节点 (Fan-out 分叉点)。
    此节点本身不做任何操作，仅作为前端和后端的并行触发起点。
    LangGraph 会自动将从此节点出发的多条边并行执行。
    """
    print("\n🔀 [分发节点] 同时派发任务给前端和后端开发 Agent...")
    return {}


def dev_check_node(state: dict) -> dict:
    """
    Fan-in 汇合节点。
    LangGraph 会自动等待前端和后端都完成后，才进入此节点。
    此节点仅检查是否有 BLOCKER 状态。
    """
    print("\n🔀 [汇合节点] 前后端代码已交齐，正在检查是否有 BLOCKER...")
    return {}


def save_experience_node(state: dict) -> dict:
    """
    经验沉淀节点：将本次项目的关键信息存入本地经验向量库。
    """
    print("\n💾 [经验沉淀] 正在总结本次项目经验并存入本地数据库...")
    summary = (
        f"项目需求: {state.get('user_requirement', 'N/A')}\n"
        f"PRD 概要: {state.get('prd', '')[:500]}\n"
        f"API 契约概要: {state.get('api_contract', '')[:500]}\n"
        f"架构审查轮数: {state.get('review_rounds', 0)}\n"
        f"开发-测试轮数: {state.get('dev_revision_count', 0)}\n"
        f"最终测试结果: {state.get('test_result', 'N/A')}"
    )
    experience_db.save_experience(summary, project_name="auto_project")
    return {"final_summary": summary}


# ==============================================================================
# 图编排 (Graph Assembly) —— 状态机的"骨架与轨道"
# ==============================================================================

def build_graph():
    """构建完整的状态机有向图"""
    workflow = StateGraph(AgentState)

    # ---- 注册所有节点 ----
    workflow.add_node("pm", pm_agent)
    workflow.add_node("architect", architect_agent)
    workflow.add_node("tech_lead", tech_lead_agent)
    workflow.add_node("dispatch", dispatch_node)        # Fan-out 分叉点
    workflow.add_node("frontend", frontend_agent)
    workflow.add_node("backend", backend_agent)
    workflow.add_node("dev_check", dev_check_node)       # Fan-in 汇合点
    workflow.add_node("qa", qa_agent)
    workflow.add_node("save_experience", save_experience_node)

    # ---- 入口 ----
    workflow.set_entry_point("pm")

    # ---- 阶段一：PM → 能力匹配检查 ----
    workflow.add_conditional_edges("pm", pm_router, {
        "architect": "architect",
        "human_intervention": END,
    })

    # ---- 阶段二：架构师 → 技术总监（红蓝对抗）----
    workflow.add_edge("architect", "tech_lead")
    workflow.add_conditional_edges("tech_lead", review_router, {
        "architect": "architect",       # 打回修改
        "dispatch": "dispatch",         # 审批通过 → 进入分发
        "human_intervention": END,      # 熔断
    })

    # ---- 阶段三：并行开发（Fan-out → Fan-in）----
    # dispatch 节点同时连向 frontend 和 backend，LangGraph 自动并行执行
    workflow.add_edge("dispatch", "frontend")
    workflow.add_edge("dispatch", "backend")

    # frontend 和 backend 都连向 dev_check，LangGraph 自动等待双方完成
    workflow.add_edge("frontend", "dev_check")
    workflow.add_edge("backend", "dev_check")

    # 汇合后检查 BLOCKER
    workflow.add_conditional_edges("dev_check", dev_check_router, {
        "architect": "architect",       # 有 BLOCKER → 回滚
        "qa": "qa",                     # 无 BLOCKER → 测试
    })

    # ---- 阶段四：QA 测试 → 交付 / 重试 ----
    workflow.add_conditional_edges("qa", qa_router, {
        "save_experience": "save_experience",   # 通过 → 沉淀经验
        "dispatch": "dispatch",                 # 失败 → 打回重做（再次并行）
        "human_intervention": END,              # 熔断
    })

    # ---- 经验沉淀 → 结束 ----
    workflow.add_edge("save_experience", END)

    return workflow


# ==============================================================================
# 主程序入口
# ==============================================================================

def main():
    print("=" * 60)
    print("🚀 终极多 Agent 状态机 v1.0")
    print("   基于 LangGraph 的智能工作流编排系统")
    print("=" * 60)

    # ---- 构建图并编译 ----
    workflow = build_graph()
    memory = MemorySaver()  # 持久化记忆（断电续传）

    app = workflow.compile(
        checkpointer=memory,
        interrupt_before=["architect"],  # PM 完成后暂停，等待人类确认 PRD
    )

    config = {"configurable": {"thread_id": "project_001"}}

    # ---- 获取用户需求 ----
    print("\n📝 请输入您的产品需求（直接回车使用默认示例）:")
    user_input = input(">>> ").strip()
    if not user_input:
        user_input = "帮我做一个网页版的待办事项清单（Todo List），支持添加、删除、标记完成"
        print(f"  使用默认需求: {user_input}")

    initial_state = {
        "user_requirement": user_input,
        "available_agents": AGENT_REGISTRY,
        "review_rounds": 0,
        "dev_revision_count": 0,
    }

    # ======================================================================
    # 第一阶段：PM 产出 PRD
    # ======================================================================
    print("\n" + "-" * 60)
    print("📋 阶段一：产品经理分析需求")
    print("-" * 60)

    for event in app.stream(initial_state, config=config, stream_mode="values"):
        pass

    # 检查是否因能力缺失而终止
    current_state = app.get_state(config)
    if current_state.values.get("missing_capability"):
        print(f"\n⚠️ 系统因能力缺口而终止: {current_state.values['missing_capability']}")
        print("请更新 config.py 中的 AGENT_REGISTRY，补充缺失的能力后重新运行。")
        return

    # 展示 PRD 并等待人类确认
    prd = current_state.values.get("prd", "")
    print("\n" + "=" * 60)
    print("⏸️  [系统挂起] PRD 已生成，等待您的审核")
    print("=" * 60)
    print(prd)
    print("=" * 60)

    confirm = input("\n✅ PRD 满意吗？输入 'y' 继续流程，输入其他内容则退出: ").strip()
    if confirm.lower() != "y":
        print("👋 已退出。您可以修改需求后重新运行。")
        return

    # ======================================================================
    # 第二至四阶段：架构设计 + 红蓝对抗 + 并发开发 + QA 测试（全自动）
    # ======================================================================
    print("\n" + "-" * 60)
    print("🏗️  阶段二～四：架构设计 → 并发开发 → 测试（全自动运行）")
    print("  包含：红蓝对抗、BLOCKER 回滚、沙盒测试、重试机制")
    print("-" * 60)

    for event in app.stream(None, config=config, stream_mode="values"):
        pass

    # ======================================================================
    # 展示最终结果
    # ======================================================================
    final_state = app.get_state(config)
    vals = final_state.values

    print("\n" + "=" * 60)
    print("🎉 项目已完成！")
    print("=" * 60)
    print(f"  📊 架构审查轮数:     {vals.get('review_rounds', 0)}")
    print(f"  🔄 开发-测试重试数:  {vals.get('dev_revision_count', 0)}")
    print(f"  ✅ 最终测试结果:     {vals.get('test_result', 'N/A')}")
    print(f"  💾 经验库累计记录:   {experience_db.list_all()} 条")
    print("=" * 60)

    # 输出生成的代码摘要
    if vals.get("frontend_code"):
        print("\n📄 [前端代码预览（前 300 字符）]:")
        print(vals["frontend_code"][:300])
        print("...")
    if vals.get("backend_code"):
        print("\n📄 [后端代码预览（前 300 字符）]:")
        print(vals["backend_code"][:300])
        print("...")

    print("\n✨ 完整代码已保存在全局 State 中。祝您开发愉快！")


if __name__ == "__main__":
    main()
