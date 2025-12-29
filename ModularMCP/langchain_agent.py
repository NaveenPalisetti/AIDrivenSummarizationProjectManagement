"""
LangChain-powered LLM Agent for ModularMCP
- Dynamic tool registration
- Session memory
- LLM-driven orchestration
"""

from langchain.agents import initialize_agent, Tool
from langchain.memory import ConversationBufferMemory
from langchain.llms import OpenAI
import requests
import os
import json

# Load agent config
CONFIG_PATH = os.environ.get('MCP_CONFIG_PATH', os.path.join(os.path.dirname(__file__), '..', 'config', 'mcp_config.json'))
with open(CONFIG_PATH, 'r') as f:
    AGENT_CONFIG = json.load(f)["agents"]

def make_tool(name, url, description):
    def _tool_func(input_str):
        resp = requests.post(url, json={"input": input_str})
        return resp.text
    return Tool(
        name=name,
        func=_tool_func,
        description=description
    )

# Register tools for each agent
TOOLS = []
if "calendar" in AGENT_CONFIG:
    TOOLS.append(make_tool(
        "Calendar",
        AGENT_CONFIG["calendar"]["create_event"],
        "Create a calendar event. Input should be a JSON string with summary, description, start, end."
    ))
if "mistral_summary" in AGENT_CONFIG:
    TOOLS.append(make_tool(
        "Summarize",
        AGENT_CONFIG["mistral_summary"]["summarize"],
        "Summarize a meeting transcript. Input should be the transcript text."
    ))
if "jira" in AGENT_CONFIG:
    TOOLS.append(make_tool(
        "Jira",
        AGENT_CONFIG["jira"]["create_issue"],
        "Create a Jira issue. Input should be a JSON string with project_key, summary, description, issuetype."
    ))
if "extractor" in AGENT_CONFIG:
    TOOLS.append(make_tool(
        "Extractor",
        AGENT_CONFIG["extractor"]["url"],
        "Extract information from text. Input should be the text to extract from."
    ))
if "task" in AGENT_CONFIG:
    TOOLS.append(make_tool(
        "Task",
        AGENT_CONFIG["task"]["url"],
        "Task management. Input should be a JSON string with task details."
    ))
if "risk" in AGENT_CONFIG:
    TOOLS.append(make_tool(
        "Risk",
        AGENT_CONFIG["risk"]["url"],
        "Risk detection. Input should be the text to analyze for risks."
    ))
if "notify" in AGENT_CONFIG:
    TOOLS.append(make_tool(
        "Notify",
        AGENT_CONFIG["notify"]["url"],
        "Send a notification. Input should be a JSON string with notification details."
    ))

# Set up LLM and memory
llm = OpenAI(temperature=0)
memory = ConversationBufferMemory(memory_key="chat_history")

# Initialize agent
agent = initialize_agent(
    TOOLS,
    llm,
    agent="chat-conversational-react-description",
    memory=memory,
    verbose=True
)

def run_agent(user_input):
    return agent.run(user_input)

if __name__ == "__main__":
    print("Welcome to ModularMCP LangChain Agent!")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            break
        response = run_agent(user_input)
        print("Agent:", response)
