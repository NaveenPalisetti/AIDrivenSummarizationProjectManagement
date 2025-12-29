

import streamlit as st
from ModularMCP.client.mcp_client import MCPClient

st.set_page_config(page_title="AI Meeting Chatbot", layout="wide")
st.title("🤖 Modular MCP LLM Chatbot")
st.caption("Conversational interface for meeting summarization, task extraction, calendar, and Jira integration.")

mcp = MCPClient()

# Initialize chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

user_input = st.chat_input("Type your request (e.g., 'Summarize this transcript...', 'Create a Jira task...', 'Show calendar events')...")

def llm_agent_response(user_message):
    # For demo: route all user input to the summarizer agent (can be extended)
    # You can add logic to detect intent and call other MCPClient methods as needed
    if "calendar" in user_message.lower():
        return mcp.get_calendar_event("primary")
    elif "jira" in user_message.lower() and ("create" in user_message.lower() or "issue" in user_message.lower()):
        # Dummy values for demo; in real use, parse user_message for details
        return mcp.create_jira_issue("DEMO", "Sample Issue", "Created from chat", "Task")
    elif "summarize" in user_message.lower() or "transcript" in user_message.lower():
        # Ask user for transcript if not present
        return {"info": "Please paste your meeting transcript to summarize."}
    else:
        # Default: echo or fallback to summarizer
        return mcp.summarize_transcript(user_message)

if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    response = llm_agent_response(user_input)
    st.session_state.chat_history.append({"role": "ai", "content": str(response)})

# Display chat history
for msg in st.session_state.chat_history:
    st.chat_message(msg["role"]).write(msg["content"])
