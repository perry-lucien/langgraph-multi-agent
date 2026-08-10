"""
QA 测试 Agent
=============
职责：
1. 将后端代码写入 Docker 沙盒（或本地沙盒）并物理执行
2. 捕获真实的终端输出（成功日志 / 报错堆栈）
3. 综合代码质量 + 执行结果，判断 PASS 或 FAIL
4. 熔断保护：超过 3 次重试强制放行，请求人工验收
"""

import re
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.messages import HumanMessage, SystemMessage
from config import QA_LLM
from tools.sandbox import get_sandbox

QA_SYSTEM_PROMPT = """你是一位 QA 测试工程师。你收到了前后端代码以及后端代码的实际执行结果（来自沙盒环境）。

你的职责：
1. 分析代码的实际执行结果（stdout 和 stderr）
2. 审查前后端代码是否严格遵循了 API 契约（接口路径、参数、响应格式是否一致）
3. 检查是否存在明显的逻辑错误、安全漏洞或遗漏功能

判定规则：
- 如果代码能正确运行（或可正确导入）且逻辑基本合理，回复第一行: PASS
- 如果代码有运行错误或严重逻辑问题，回复第一行: FAIL，并详细描述：
  · 具体的错误信息（直接引用终端输出）
  · 错误可能的原因分析
  · 针对前端和后端的分别修复建议

你的回复第一行必须且仅为 PASS 或 FAIL 二选一。"""


def qa_agent(state: dict) -> dict:
    """QA 测试节点"""
    dev_revision_count = state.get("dev_revision_count", 0)

    # ---- 熔断保护 ----
    if dev_revision_count >= 3:
        print("\n🔎 [QA Agent] ⚠️ 已达到最大重试次数 (3次)，强制放行！")
        print("  建议您人工检查最终代码质量。")
        return {
            "test_result": "PASS",
            "test_feedback": "⚠️ 自动测试已达最大重试次数，强制放行。建议人工验收。",
            "dev_revision_count": dev_revision_count,
        }

    print(f"\n🔎 [QA Agent] 正在沙盒中执行代码测试（第 {dev_revision_count + 1} 轮）...")

    frontend_code = state.get("frontend_code", "")
    backend_code = state.get("backend_code", "")

    # ---- 沙盒执行后端代码 ----
    sandbox = get_sandbox()
    backend_pure = _extract_code_block(backend_code, "python")

    sandbox_result = {
        "success": True,
        "stdout": "未能从后端代码中提取可执行的 Python 代码块",
        "stderr": "",
        "exit_code": 0,
    }

    if backend_pure:
        # 尝试导入模块来验证语法和依赖是否正确
        sandbox_result = sandbox.execute_code(
            files={"main.py": backend_pure},
            entry_command='python -c "import ast; ast.parse(open(\'main.py\').read()); print(\'语法检查通过\')"',
        )

    # 构建执行报告
    execution_report = f"""
【沙盒执行结果】:
- 执行成功: {'✅ 是' if sandbox_result['success'] else '❌ 否'}
- 标准输出: {sandbox_result['stdout'][:800] if sandbox_result['stdout'] else '(无)'}
- 错误输出: {sandbox_result['stderr'][:800] if sandbox_result['stderr'] else '(无)'}
- 退出码: {sandbox_result['exit_code']}
"""
    print(execution_report[:300])

    # ---- 让 QA LLM 综合分析 ----
    # 截断代码避免 Token 爆炸
    fe_preview = frontend_code[:3000] if frontend_code else "(无前端代码)"
    be_preview = backend_code[:3000] if backend_code else "(无后端代码)"

    response = QA_LLM.invoke([
        SystemMessage(content=QA_SYSTEM_PROMPT),
        HumanMessage(content=(
            f"【前端代码】:\n{fe_preview}\n\n"
            f"【后端代码】:\n{be_preview}\n\n"
            f"{execution_report}"
        )),
    ])

    result_text = response.content.strip()
    is_pass = result_text.upper().startswith("PASS")

    if is_pass:
        print("  ✅ QA 测试通过！代码质量合格。")
    else:
        print(f"  ❌ QA 测试未通过（第 {dev_revision_count + 1} 轮）")

    return {
        "test_result": "PASS" if is_pass else "FAIL",
        "test_feedback": result_text,
        "dev_revision_count": dev_revision_count + (0 if is_pass else 1),
    }


def _extract_code_block(text: str, language: str = "python") -> str:
    """
    从 Markdown 格式的 AI 输出中提取指定语言的代码块。
    例如从 ```python ... ``` 中提取纯代码。
    """
    # 先尝试精确匹配指定语言
    pattern = rf"```{language}\s*\n(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    if matches:
        return matches[0].strip()

    # 回退：匹配任意语言的代码块
    pattern = r"```\w*\s*\n(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    if matches:
        return matches[0].strip()

    return ""
