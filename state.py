"""
全局状态黑板 (State) 定义
=========================
这是整个多 Agent 状态机的"接力棒"。
每个子代理执行完毕后，会将自己的工作成果写入对应字段。
母代理（路由器）通过检查这些字段来决定下一步调用谁。
"""

from typing import TypedDict


class AgentState(TypedDict, total=False):
    """
    全局状态类型定义。
    total=False 表示所有字段都是可选的（初始时大部分为空）。
    """

    # ---- 阶段一：需求与策划 ----
    user_requirement: str               # 用户原始需求
    available_agents: list              # 子代理能力注册表（由 config.py 提供）
    prd: str                            # 产品经理输出的 PRD（产品需求文档）
    missing_capability: str             # PM 发现的缺失能力（非空时触发人工介入）

    # ---- 阶段二：架构设计 ----
    api_contract: str                   # 架构师输出的 API 接口契约
    review_status: str                  # 技术总监审批状态: "APPROVED" / "REJECTED"
    review_feedback: str                # 技术总监的具体修改建议
    review_rounds: int                  # 架构师与总监的对抗轮数（熔断上限 3）

    # ---- 阶段三：并发开发 ----
    frontend_code: str                  # 前端代码
    backend_code: str                   # 后端代码
    blocker: str                        # 开发遇到的死胡同信号（非空时触发回滚至架构师）

    # ---- 阶段四：测试与交付 ----
    test_result: str                    # QA 测试结果: "PASS" / "FAIL"
    test_feedback: str                  # QA 测试反馈详情（含真实终端输出）
    dev_revision_count: int             # 开发-测试重试计数（熔断上限 3）

    # ---- 经验沉淀 ----
    final_summary: str                  # 项目最终总结（存入经验库）
