from mcp.core.mcp import MCPTool, MCPToolType
from mcp.tools.llm_task_extraction import extract_tasks_jira_format
from mcp.tools.nlp_task_extraction import extract_tasks_nlp

class TaskTool(MCPTool):
    def __init__(self):
        super().__init__(
            tool_id="task",
            tool_type=MCPToolType.TASK_MANAGER,
            name="Task Extractor",
            description="Extracts tasks from meeting transcripts using LLM or NLP.",
            api_endpoint="/mcp/task",
            auth_required=False,
            parameters={"transcript": "str", "method": "str"}
        )

    async def execute(self, params):
        transcript = params.get("transcript", "")
        method = params.get("method", "llm")
        if method == "llm":
            tasks = extract_tasks_jira_format(transcript)
        else:
            tasks = extract_tasks_nlp(transcript)
        return {"status": "success", "tasks": tasks}
