import os
import docker
import sys

# 尝试从所有可能的路径导入 AgentExecutor
try:
    from langchain.agents import AgentExecutor
except ImportError:
    try:
        from langchain.agents.executor import AgentExecutor
    except ImportError:
        print("错误：无法找到 AgentExecutor。请确保运行了 pip install langchain")
        sys.exit(1)

from langchain.agents import create_tool_calling_agent
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# ==========================================
# 1. 配置区
# ==========================================
#os.environ["OPENAI_API_KEY"] = "sk-vatiqisytlgueqalungbjzuitwzrxcyajpsupzwglwynoowv" # 建议完成后更换
#os.environ["OPENAI_API_BASE"] = "https://api.siliconflow.cn/v1"
#MODEL_NAME = "Qwen/Qwen2.5-7B-Instruct" 

os.environ["OPENAI_API_KEY"] = "3ed1a615a0f14902b1b40ae112d599bf.19UVS6QGKZLklasM" 
# 智谱的 API 地址
os.environ["OPENAI_API_BASE"] = "https://open.bigmodel.cn/api/paas/v4/"

# 使用智谱最快、最适合做 Agent 的免费/低价模型
MODEL_NAME = "glm-4-flash"

client = docker.from_env()

# ==========================================
# 2. 工具定义
# ==========================================
@tool
def list_services():
    """发现异常：获取所有 NetBox 容器的运行状态和健康检查结果。"""
    try:
        containers = client.containers.list(all=True)
        res = [{"name": c.name, "status": c.status, "health": c.attrs.get('State', {}).get('Health', {}).get('Status', 'N/A')} for c in containers]
        return str(res)
    except Exception as e:
        return f"获取服务列表失败: {str(e)}"

@tool
def diagnose_service(container_name: str):
    """给出诊断建议：提取指定容器的最后50行日志进行分析。"""
    try:
        container = client.containers.get(container_name)
        logs = container.logs(tail=50).decode('utf-8')
        return f"Container Logs for {container_name}:\n{logs}"
    except Exception as e:
        return f"诊断失败: {str(e)}"

@tool
def take_action(container_name: str, action: str):
    """采取处置动作：对容器执行 restart, start 操作。"""
    try:
        c = client.containers.get(container_name)
        if action == "restart": c.restart()
        elif action == "start": c.start()
        return f"执行动作 {action} 成功于 {container_name}"
    except Exception as e:
        return f"动作执行失败: {str(e)}"

# ==========================================
# 3. Agent 构建
# ==========================================
prompt = ChatPromptTemplate.from_messages([
    ("system", """你是一个严谨的 AI Native SRE 专家。在处理环境问题时，你必须严格遵守以下 SOP：

1. **发现阶段 (Discovery)**：
   - 调用 list_services 获取所有容器状态。
   - 识别出处于 'exited'、'unhealthy' 或任何非 'running' 状态的服务。

2. **诊断与建议阶段 (Diagnosis & Suggestion)**：
   - 对于发现的异常服务，**必须**调用 diagnose_service 查看详细日志。
   - **重要：** 在采取任何修复动作之前，你必须以文本形式向用户汇报：
     - [故障原因分析]：根据日志判断为什么服务挂了。
     - [处置建议]：你计划执行什么操作，以及为什么。

3. **处置阶段 (Remediation)**：
   - 只有在给出了诊断建议后，才能调用 take_action 工具进行修复。

4. **验证阶段 (Verification)**：
   - 修复后，再次调用 list_services 确认服务是否变回 'healthy' 状态。

请确保你的最终回答包含以上完整的全过程。"""),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

llm = ChatOpenAI(model=MODEL_NAME, temperature=0)
tools = [list_services, diagnose_service, take_action]
agent = create_tool_calling_agent(llm, tools, prompt)

executor = AgentExecutor(
    agent=agent, 
    tools=tools, 
    verbose=True,
    handle_parsing_errors=True
)

if __name__ == "__main__":
    print(f"--- SRE Agent 开始巡检 ({MODEL_NAME}) ---")
    executor.invoke({"input": "检查 NetBox 环境，如果发现任何不正常的情况，请诊断并修复它。"})
