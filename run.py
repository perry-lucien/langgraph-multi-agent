"""
程序化调用入口 (Python API & 命令行一键调用)
============================================
供其他 Python 脚本、Agent 或命令行直接调用，无需手动在终端交互。

使用方法:
  1. 命令行调用:
     python run.py "帮我做一个网页版计算器"

  2. Python 代码中导入调用:
     from run import run_workflow
     result = run_workflow("帮我做一个网页版计算器", auto_approve_prd=True)
"""

import sys
import os
import argparse

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from langgraph.checkpoint.memory import MemorySaver
from main import build_graph, experience_db
from config import AGENT_REGISTRY


def run_workflow(user_requirement: str, auto_approve_prd: bool = True) -> dict:
    """
    程序化运行多 Agent 状态机工作流

    Args:
        user_requirement: 产品需求描述字符串
        auto_approve_prd: 是否自动批准 PRD (默认 True，方便 Agent 全自动运行)

    Returns:
        包含 PRD、API契约、前后端代码及测试结果的最终状态字典
    """
    print("=" * 60)
    print("🚀 启动多 Agent 状态机工作流")
    print(f"  📝 需求: {user_requirement}")
    print("=" * 60)

    workflow = build_graph()
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)

    config = {"configurable": {"thread_id": "api_run_001"}}

    initial_state = {
        "user_requirement": user_requirement,
        "prd_approved": auto_approve_prd,
        "available_agents": AGENT_REGISTRY,
        "review_rounds": 0,
        "dev_revision_count": 0,
    }

    # 运行全流程
    for _ in app.stream(initial_state, config=config, stream_mode="values"):
        pass

    final_state = app.get_state(config)
    vals = final_state.values

    print("\n" + "=" * 60)
    print("🎉 执行完毕！")
    print(f"  ✅ 测试结果: {vals.get('test_result', 'N/A')}")
    print("=" * 60)

    return {
        "prd": vals.get("prd", ""),
        "api_contract": vals.get("api_contract", ""),
        "frontend_code": vals.get("frontend_code", ""),
        "backend_code": vals.get("backend_code", ""),
        "test_result": vals.get("test_result", ""),
        "review_rounds": vals.get("review_rounds", 0),
        "dev_revision_count": vals.get("dev_revision_count", 0),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="多 Agent 状态机命令行快捷调用")
    parser.add_argument("requirement", type=str, nargs="?", help="产品需求描述")
    args = parser.parse_args()

    req = args.requirement or "做一个简单的待办事项网页应用"
    run_workflow(req, auto_approve_prd=True)
