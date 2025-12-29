
import streamlit as st
from ModularMCP.client.mcp_client import MCPClient

st.title("Modular MCP System UI")

mcp = MCPClient()

st.header("1. Create Calendar Event")
summary = st.text_input("Event Summary")
description = st.text_area("Event Description / Transcript")
start = st.text_input("Start DateTime (ISO format)")
end = st.text_input("End DateTime (ISO format)")
if st.button("Create Calendar Event"):
    resp = mcp.create_calendar_event(summary, description, start, end)
    st.write(resp)

st.header("2. Summarize Transcript")
transcript = st.text_area("Paste meeting transcript:")
if st.button("Summarize Transcript"):
    resp = mcp.summarize_transcript(transcript)
    st.write(resp)

st.header("3. Create Jira Issue")
project_key = st.text_input("Jira Project Key", value="DEMO")
issue_summary = st.text_input("Jira Issue Summary")
issue_description = st.text_area("Jira Issue Description")
issuetype = st.text_input("Jira Issue Type", value="Task")
if st.button("Create Jira Issue"):
    resp = mcp.create_jira_issue(project_key, issue_summary, issue_description, issuetype)
    st.write(resp)
