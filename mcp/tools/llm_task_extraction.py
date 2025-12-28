"""
LLM-based Task Extraction Tool for MCP
Outputs tasks in Jira issue format using a local BART model.
"""



# Use Mistral for LLM-based task extraction
from mcp.agents.mistral_summarizer import summarize_with_mistral
from mcp.agents.summarization_agent import get_mistral_model


def extract_tasks_jira_format(transcript, session_action_items=None):
    """
    If session_action_items is provided and non-empty, use them directly.
    Otherwise, run Mistral extraction as before.
    """
    if session_action_items and isinstance(session_action_items, list) and len(session_action_items) > 0:
        print("[DEBUG] Using action_items from session, skipping Mistral extraction.")
        return session_action_items
    mistral_tokenizer, mistral_model = get_mistral_model()
    # Use a prompt tailored for Jira task extraction
    prompt = (
        "Extract up to 3 action items or tasks from the following meeting transcript. "
        "For each, output in Jira issue format as strictly as possible, one after another, with each field on its own line.\n"
        "- Summary: <short summary>\n"
        "- Description: <detailed description>\n"
        "- Assignee: <person, if mentioned>\n"
        "- Due Date: <date, if mentioned>\n"
        "Transcript:\n"
        f"{transcript}\n"
        "Tasks:"
    )
    # Use the same chunking and summarization logic as summarize_with_mistral, but for this prompt
    result = summarize_with_mistral(mistral_tokenizer, mistral_model, prompt, meeting_id="jira_task_extraction")
    # Try to parse action items from the result (reuse action_items if present, else parse from summary_text)
    action_items = result.get("action_items", [])
    if not action_items:
        # Fallback: try to parse from summary_text if model didn't return action_items
        def parse_tasks(text):
            tasks = []
            current_task = {}
            for line in text if isinstance(text, list) else text.splitlines():
                line = line.strip()
                if line.startswith('- Summary:'):
                    if current_task:
                        tasks.append(current_task)
                        current_task = {}
                    current_task['Summary'] = line[len('- Summary:'):].strip()
                elif line.startswith('- Description:'):
                    current_task['Description'] = line[len('- Description:'):].strip()
                elif line.startswith('- Assignee:'):
                    current_task['Assignee'] = line[len('- Assignee:'):].strip()
                elif line.startswith('- Due Date:'):
                    current_task['Due Date'] = line[len('- Due Date:'):].strip()
            if current_task:
                tasks.append(current_task)
            return tasks
        action_items = parse_tasks(result.get("summary_text", []))
    # Final fallback: if still empty, try to extract from transcript
    if not action_items:
        print("[DEBUG][LLM Task Extraction] No action items found in model output or summary, extracting from transcript as fallback.")
        lines = [l.strip() for l in transcript.replace('\n', '. ').split('.') if l.strip()]
        action_keywords = ['fix', 'complete', 'implement', 'create', 'update', 'assign', 'test', 'review', 'prepare', 'set up', 'ensure', 'action item', 'task']
        action_items = [l for l in lines if any(k in l.lower() for k in action_keywords)]
        print(f"[DEBUG][LLM Task Extraction] Fallback extracted action_items from transcript: {action_items}")
    return action_items

if __name__ == "__main__":
    transcript = "Your transcript text here..."
    print(extract_tasks_jira_format(transcript))