# AI Native SRE Agent: NetBox 故障自愈系统

## 1. 项目背景
本项目是一个基于 **Tool Calling** 结构的智能运维 Agent。

不同于传统的硬编码脚本，本项目利用大语言模型（LLM）的推理能力，实现了从**“发现异常”**到**“诊断建议”**再到**“采取处置”**的完整 SRE 闭环。

## 2. 核心架构：SRE 闭环逻辑
Agent 严格遵循以下三个阶段进行工作：

1.  **发现异常 (Discovery)**: 通过调用 `list_services` 工具，感知 Docker 容器栈的运行状态（Status）与健康检查（Health）数据。
2.  **诊断建议 (Diagnosis & Suggestion)**: 识别异常后，Agent 主动调用 `diagnose_service` 读取实时日志，利用 LLM 分析故障根本原因（Root Cause），并向用户输出诊断报告与处置方案。
3.  **采取处置 (Remediation)**: 在建立逻辑闭环后，Agent 调用 `take_action` 工具执行具体的修复动作（如重启容器、启动依赖项等），并验证修复结果。

## 3. 技术栈
*   **开发语言**: Python 3.12+
*   **Agent 框架**: LangChain (create_tool_calling_agent)
*   **基础设施控制**: Docker SDK for Python
*   **推理大脑**: LLM (GLM-4 / DeepSeek / Qwen via OpenAI API protocol)
*   **运行环境**: GitHub Codespaces / Linux

## 4. 快速开始

### 4.1 环境准备
在 GitHub Codespaces 或 Linux 环境中，启动 NetBox 容器栈：
```bash
docker compose up -d
```

### 4.2 安装依赖
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install langchain langchain-openai langchain-community docker
```

### 4.3 配置与运行
1. 修改 `sre_agent.py` 中的 `OPENAI_API_KEY` 与 `OPENAI_API_BASE`。
2. 运行 Agent：
```bash
python sre_agent.py
```

## 5. 工具箱 (Tools) 说明
Agent 具备以下原子化能力：
*   `list_services`: 扫描 Docker Engine，获取所有服务的健康画像。
*   `diagnose_service`: 进入容器内部，抓取最后 50 行异常日志。
*   `take_action`: 执行生命周期管理操作（start / restart）。

## 6. 故障模拟测试 (Proof of Concept)
为了验证 Agent 的闭环能力，可执行以下操作：

1.  **制造故障**: 手动停止 Redis 容器：`docker stop netbox-docker-redis-1`。
2.  **Agent 执行**:
    *   **Action**: 调用 `list_services` 发现 `redis` 容器 `exited`。
    *   **Thought**: 分析故障并输出：“Redis 容器异常停止，可能导致 NetBox 缓存失效，建议立即重启。”
    *   **Action**: 调用 `take_action` 执行 `restart`。
    *   **Observation**: 再次检查，状态恢复 `healthy`。

## 7. 为什么这是 AI-Native SRE？
*   **自主决策**: Agent 不是根据预设的 `if-else` 运行，而是根据 LLM 对工具返回结果的实时理解来决定下一步操作。
*   **语义诊断**: 能够理解日志文本中的“Connection Refused”或“Authentication Error”等语义，并给出人性化的建议。
*   **原子化工具化**: 将基础设施操作解耦为工具，使 Agent 能够应对复杂的、非线性的故障场景。
