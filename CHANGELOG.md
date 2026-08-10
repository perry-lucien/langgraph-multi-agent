# 📝 Changelog / 版本日志

本文件记录每次版本更新的内容，方便追踪改动历史。

格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/) 规范。

---

## [1.0.0] - 2026-08-11

### 🎉 首次发布

#### 新增 (Added)
- **母子代理架构**：基于 LangGraph StateGraph 的完整多 Agent 编排系统
- **产品经理 Agent**：合并设计与策划，一气呵成输出 PRD
- **架构师 Agent**：根据 PRD 输出前后端 API 接口契约
- **技术总监 Agent**：红蓝对抗审查 API 契约，输出 APPROVED/REJECTED
- **前端开发 Agent**：严格按 API 契约编写前端代码
- **后端开发 Agent**：严格按 API 契约编写后端 Python/FastAPI 代码
- **QA 测试 Agent**：Docker 沙盒物理执行代码 + 代码审查
- **并行开发支持**：前后端通过 Fan-out/Fan-in 模式并发执行
- **契约驱动开发**：前后端共享同一份 API 契约，确保接口一致
- **Docker 沙盒执行器**：在 Docker 容器中安全执行代码，自动回退本地沙盒
- **本地经验向量库**：基于 ChromaDB 的跨项目经验记忆系统
- **能力注册表**：PM Agent 自动检测团队能力缺口
- **六重防护机制**：
  - 能力缺失检测
  - 架构对抗熔断（≥3 轮）
  - 开发 BLOCKER 回滚
  - 测试重试熔断（≥3 次）
  - 沙盒执行超时（30 秒）
  - Checkpoint 断电续传
- **异构模型配置**：支持 OpenAI / OpenAI 兼容 / Anthropic 三种 API 格式
- **人工确认断点**：PM 输出 PRD 后自动暂停，等待用户审核确认

---

<!-- 
## [1.1.0] - YYYY-MM-DD

### 新增 (Added)
- 

### 变更 (Changed)
- 

### 修复 (Fixed)
- 

### 移除 (Removed)
- 
-->
