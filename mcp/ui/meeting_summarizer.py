"""
Summarization logic for MCP Streamlit App
"""
from mcp.core.mcp import MCPHost

from mcp.tools.summarization_tool import SummarizationTool
from mcp.tools.mcp_calendar_tool import get_calendar_transcripts
from mcp.tools.llm_task_extraction import extract_tasks_jira_format
from mcp.tools.nlp_task_extraction import extract_tasks_nlp
from mcp.tools.followup_meeting import check_and_create_followup_meeting

from mcp.tools.calendar_tool import CalendarTool
from mcp.tools.task_tool import TaskTool
from mcp.tools.followup_tool import FollowupTool

def summarize_meeting(transcript, meeting_id, mode="auto"):
    mcp_host = MCPHost()
    # Register all relevant tools
    summ_tool = SummarizationTool(mode=mode)
    calendar_tool = CalendarTool()
    task_tool = TaskTool()
    followup_tool = FollowupTool()
    mcp_host.register_tool(summ_tool)
    mcp_host.register_tool(calendar_tool)
    mcp_host.register_tool(task_tool)
    mcp_host.register_tool(followup_tool)
    session_id = mcp_host.create_session(agent_id="ui_agent")
    params = {"transcript": transcript, "meeting_id": meeting_id, "mode": mode}
    import asyncio
    result = asyncio.run(mcp_host.execute_tool(session_id, tool_id="summarization", parameters=params))
    mcp_host.end_session(session_id)
    return result
