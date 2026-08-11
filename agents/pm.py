"""
产品经理 (PM) Agent
===================
职责（合并了设计 + 策划，一气呵成）：
1. 接收用户需求，查阅经验库获取历史避坑参考
2. 读取能力注册表，检查现有子代理能否胜任
3. 若发现缺失能力 → 设置 missing_capability 标记，触发人工介入
4. 输出包含功能设计 + 阶段规划的完整 PRD（产品需求文档）
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.messages import HumanMessage, SystemMessage
from config import PM_LLM, AGENT_REGISTRY
from memory.experience_db import ExperienceDB

experience_db = ExperienceDB()

PM_SYSTEM_PROMPT = """你是一位资深产品经理 (PM)。你的职责是：

1. 【理解需求】深入分析用户的需求描述，补充用户未提及但必要的功能细节。
2. 【查阅经验】如果提供了历史项目经验，参考其中的避坑建议。
3. 【能力匹配】你会收到一份当前团队的「能力注册表」，列出了所有可用子代理及其擅长领域。
   - 如果所有需求都能被现有团队覆盖，正常输出 PRD。
   - 如果发现某个关键需求无法被任何现有子代理胜任（例如需要 iOS 原生开发但团队没有），
     你必须在输出的最后一行附加：
     MISSING_CAPABILITY: <缺失的能力描述>
4. 【输出 PRD】输出一份简洁但完整的产品需求文档（PRD），包含：
   - 产品概述与目标用户
   - 核心功能列表（按优先级排列）
   - 页面/模块设计要点
   - 交互逻辑与用户流程
   - 分阶段开发计划（Roadmap）
   - 技术栈建议

请确保 PRD 条理清晰、逻辑严密，方便架构师直接据此设计 API 接口。"""


def pm_agent(state: dict) -> dict:
    """产品经理节点"""
    print("\n📋 [产品经理 Agent] 正在分析需求、查阅经验、匹配团队能力...")

    requirement = state["user_requirement"]
    agents_info = state.get("available_agents", AGENT_REGISTRY)

    # 1. 查阅历史经验
    past_experiences = experience_db.search_experience(requirement)
    experience_text = ""
    if past_experiences:
        experience_text = "\n\n【历史项目经验参考】:\n" + "\n---\n".join(past_experiences)
        print(f"  📚 找到 {len(past_experiences)} 条相关历史经验")
    else:
        print("  📚 经验库暂无相关记录（首次运行为空属正常）")

    # 2. 格式化能力注册表
    registry_text = "\n".join([
        f"- {a['name']}: {a['description']}（擅长: {', '.join(a['capabilities'])}）"
        for a in agents_info
    ])

    # 3. 构建 Prompt 并调用 LLM
    user_message = f"""【用户需求】: {requirement}

【当前团队能力注册表】:
{registry_text}
{experience_text}

请输出完整的 PRD 产品需求文档。如果发现团队能力缺口，务必在最后附加 MISSING_CAPABILITY 标记。"""

    response = PM_LLM.invoke([
        SystemMessage(content=PM_SYSTEM_PROMPT),
        HumanMessage(content=user_message),
    ])

    prd_content = response.content

    # 4. 检测是否标记了能力缺失
    missing = ""
    if "MISSING_CAPABILITY:" in prd_content:
        for line in prd_content.split("\n"):
            if "MISSING_CAPABILITY:" in line:
                val = line.split("MISSING_CAPABILITY:")[-1].strip()
                if val and val.lower() not in ["无", "none", "no", "无。"]:
                    missing = val
                break

    result = {"prd": prd_content}
    if missing:
        result["missing_capability"] = missing
        print(f"  ⚠️ 发现能力缺口: {missing}")
    else:
        print("  ✅ 团队能力完全匹配需求")

    return result
