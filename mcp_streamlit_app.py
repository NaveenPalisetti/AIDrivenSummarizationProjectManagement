
import streamlit as st
from mcp.ui.meeting_summarizer import summarize_meeting
from mcp.agents.llm_task_manager_agent import LLMTaskManagerAgent
from mcp.tools.nlp_task_extraction import extract_tasks_nlp
from mcp.tools.llm_task_extraction import extract_tasks_jira_format
from mcp.tools.mcp_calendar_tool import get_calendar_transcripts


st.set_page_config(page_title="AI Meeting Management", layout="wide")
st.title("🤖 AI Meeting Manager (Conversational)")
st.caption("Powered by SummarizationAgent, TaskManagerAgent, RiskDetectionAgent")

# --- Status/Info Panel ---
tools_loaded = [
    "Summarization (BART, LLM, Mistral)",
    "Task Extraction (NLP, LLM)",
    "Calendar Integration",
    "Jira Integration"
]
st.info(f"**Tools loaded:** {len(tools_loaded)} ({', '.join(tools_loaded)})")

session_info = f"**Session:** Meeting ID: `{st.session_state.get('meeting_id', 'N/A')}` | Summarization Mode: `{st.session_state.get('summarization_mode', 'auto')}` | Next Action: `{st.session_state.get('next_action', 'N/A')}`"
st.markdown(session_info)

# --- Conversational Chat Section ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "next_action" not in st.session_state:
    st.session_state.next_action = None
if "transcript" not in st.session_state:
    st.session_state.transcript = None
if "meeting_id" not in st.session_state:
    st.session_state.meeting_id = "chat_session"
if "summary" not in st.session_state:
    st.session_state.summary = None
if "tasks" not in st.session_state:
    st.session_state.tasks = None


# Summarization modes and task extraction methods
SUMMARIZATION_MODES = ["auto", "llm", "bart", "mistral"]
TASK_EXTRACTION_METHODS = ["NLP (spaCy)", "LLM (Jira format)"]

# Calendar event selection state
if "calendar_transcripts" not in st.session_state:
    st.session_state.calendar_transcripts = []
if "calendar_event_titles" not in st.session_state:
    st.session_state.calendar_event_titles = []
if "selected_calendar_event" not in st.session_state:
    st.session_state.selected_calendar_event = None
if "summarization_mode" not in st.session_state:
    st.session_state.summarization_mode = SUMMARIZATION_MODES[0]
if "task_extraction_method" not in st.session_state:
    st.session_state.task_extraction_method = TASK_EXTRACTION_METHODS[0]

user_input = st.chat_input("Type your request (e.g., 'Summarize meeting', 'Extract tasks', 'Show calendar events', 'Create Jira tasks')...")

def ai_message(msg):
    # If the message is a dict with summary/action_items, format it nicely
    print("[DEBUG][ai_message] msg:", msg)
    if isinstance(msg, dict) and ("summary_text" in msg or "summary" in msg or "action_items" in msg):
        content = ""
        # Show summary as readable text (support both 'summary_text' and 'summary' keys)
        summary_val = msg.get("summary_text") if "summary_text" in msg else msg.get("summary")
        if summary_val:
            content += "**Summary:**\n"
            if isinstance(summary_val, list):
                for item in summary_val:
                    content += f"- {item}\n"
            else:
                content += f"{summary_val}\n"
        # Show action items as readable text
        if "action_items" in msg and msg["action_items"]:
            content += "\n**Action Items:**\n"
            for item in msg["action_items"]:
                if isinstance(item, dict):
                    # Try common keys for task/action item
                    task = item.get('task') or item.get('summary') or ''
                    owner = item.get('owner') or item.get('assignee') or ''
                    deadline = item.get('deadline') or item.get('due_date') or ''
                    content += f"- **Task:** {task}"
                    if owner:
                        content += f"  **Owner:** {owner}"
                    if deadline:
                        content += f"  **Deadline:** {deadline}"
                    content += "\n"
                else:
                    content += f"- {item}\n"
        st.session_state.chat_history.append({"role": "ai", "content": content.strip()})
    else:
        st.session_state.chat_history.append({"role": "ai", "content": msg})

def user_message(msg):
    st.session_state.chat_history.append({"role": "user", "content": msg})


if user_input:
    user_message(user_input)
    # Calendar event selection
    if st.session_state.next_action == "select_calendar_event" and user_input.strip().lower().startswith("event"):
        try:
            idx = int(user_input.strip().split()[-1]) - 1
            transcript = st.session_state.calendar_transcripts[idx]
            st.session_state.transcript = transcript
            st.session_state.selected_calendar_event = idx
            ai_message(f"Transcript for Event {idx+1} loaded. Please choose a summarization mode: {', '.join(SUMMARIZATION_MODES)}.")
            st.session_state.next_action = "choose_summarization_mode"
        except Exception:
            ai_message(f"Invalid event selection. Please type one of: {',  '.join(st.session_state.calendar_event_titles)}")
            st.session_state.next_action = "select_calendar_event"
    elif "calendar" in user_input.lower() or ("event" in user_input.lower() and st.session_state.next_action is None):
        ai_message("Fetching Google Calendar event transcripts. Please wait...")
        transcripts = get_calendar_transcripts(days_back=7, days_forward=1, calendar_id="primary")
        st.session_state.calendar_transcripts = transcripts
        # Try to extract event titles if available in the transcript dicts, else use generic names
        event_titles = []
        for i, t in enumerate(transcripts):
            title = None
            if isinstance(t, dict):
                title = t.get('title') or t.get('summary') or t.get('meeting_title')
            if not title:
                # Try to extract a first line or fallback
                if isinstance(t, str):
                    title = t.strip().split('\n')[0][:60]
                else:
                    title = f"Event {i+1}"
            event_titles.append(f"Event {i+1}: {title}")
        st.session_state.calendar_event_titles = event_titles
        if transcripts:
            ai_message(f"Found {len(transcripts)} event transcripts:\n{',  '.join(event_titles)}\nPlease type the event number as shown above (e.g., 'Event 1') to select.")
            st.session_state.next_action = "select_calendar_event"
        else:
            ai_message("No transcripts found for the selected range.")
            st.session_state.next_action = None
    elif st.session_state.next_action == "choose_summarization_mode" and user_input.strip().lower() in SUMMARIZATION_MODES:
        st.session_state.summarization_mode = user_input.strip().lower()
        ai_message(f"Summarizing with mode '{st.session_state.summarization_mode}'. Please wait...")
        try:
            print("[DEBUG] Calling summarize_meeting with transcript:", st.session_state.transcript)
            result = summarize_meeting(st.session_state.transcript, st.session_state.meeting_id, mode=st.session_state.summarization_mode)
            print("[DEBUG] summarize_meeting result:", result)
            st.session_state.summary = result.get("summary_text", "")
            # Display only summary and action items in chat
            ai_message(result)
            # If action_items are present, use them as tasks and go directly to review/creation
            action_items = result.get("action_items", [])
            print("[DEBUG] Extracted action_items:", action_items)
            if action_items:
                st.session_state.tasks = action_items
                ai_message("Extracted action items from summary:")
                # Always try to show as a table if all are dicts
                shown_table = False
                if all(isinstance(t, dict) for t in action_items):
                    import pandas as pd
                    df = pd.DataFrame(action_items)
                    print("[DEBUG] Action items DataFrame:\n", df)
                    with st.chat_message("ai"):
                        if not df.empty:
                            st.write("Here are the extracted action items:")
                            st.table(df)
                            shown_table = True
                        else:
                            st.info("No action item information to display.")
                # Always also show as readable list
                with st.chat_message("ai"):
                    st.write("**Action Items (List):**")
                    for i, t in enumerate(action_items, 1):
                        if isinstance(t, dict):
                            task = t.get('task') or t.get('summary') or ''
                            owner = t.get('owner') or t.get('assignee') or ''
                            deadline = t.get('deadline') or t.get('due_date') or ''
                            print(f"[DEBUG] Action Item {i}: task={task}, owner={owner}, deadline={deadline}")
                            st.write(f"{i}. Task: {task} | Owner: {owner} | Deadline: {deadline}")
                        else:
                            print(f"[DEBUG] Action Item {i}: {t}")
                            st.write(f"{i}. {t}")
                ai_message("Please review the action items above. Type the task numbers you want to create in Jira (e.g., '1,3' for Task 1 and Task 3), or 'all' to create all. Type 'show tasks' to see the list again.")
                st.session_state.next_action = "select_tasks_to_create"
            else:
                print("[DEBUG] No action items found in summary.")
                ai_message(f"No action items found in summary. Would you like to extract tasks? Available methods: {', '.join(TASK_EXTRACTION_METHODS)}.")
                st.session_state.next_action = "choose_task_extraction_method"
        except Exception as e:
            print(f"[DEBUG] Error during summarization: {e}")
            ai_message(f"Error during summarization: {e}")
            st.session_state.next_action = None
    elif st.session_state.next_action == "choose_task_extraction_method" and user_input.strip() in TASK_EXTRACTION_METHODS:
        st.session_state.task_extraction_method = user_input.strip()
        ai_message(f"Extracting tasks using '{st.session_state.task_extraction_method}'. Please wait...")
        try:
            if st.session_state.task_extraction_method == "LLM (Jira format)":
                tasks = extract_tasks_jira_format(st.session_state.transcript)
            else:
                tasks = extract_tasks_nlp(st.session_state.transcript)
            st.session_state.tasks = tasks
            # Display extracted tasks with all fields in a table
            if tasks:
                ai_message("Extracted tasks:")
                # If all tasks are dicts, show as a single table
                if all(isinstance(t, dict) for t in tasks):
                    import pandas as pd
                    df = pd.DataFrame(tasks)
                    if not df.empty:
                        # Show the table as part of the chat flow
                        with st.chat_message("ai"):
                            st.write("Here are the extracted tasks:")
                            st.table(df)
                        ai_message("Please review the table above. Type the task numbers you want to create in Jira (e.g., '1,3' for Task 1 and Task 3), or 'all' to create all. Type 'show tasks' to see this table again.")
                    else:
                        with st.chat_message("ai"):
                            st.info("No task information to display.")
                        ai_message("No task information to display. Please try extracting again.")
                else:
                    for i, t in enumerate(tasks, 1):
                        st.markdown(f"**Task {i}:** {t}")
                    ai_message("Please type the task numbers you want to create in Jira (e.g., '1,3' for Task 1 and Task 3), or 'all' to create all. Type 'show tasks' to see the list again.")
                st.session_state.next_action = "select_tasks_to_create"
            else:
                ai_message("No tasks found.")
                st.session_state.next_action = None
        except Exception as e:
            ai_message(f"Error during task extraction: {e}")
            st.session_state.next_action = None
    elif st.session_state.next_action == "await_transcript":
        st.session_state.transcript = user_input
        ai_message(f"Please choose a summarization mode: {', '.join(SUMMARIZATION_MODES)}.")
        st.session_state.next_action = "choose_summarization_mode"
    elif st.session_state.next_action == "post_summary" and ("task" in user_input.lower() or "extract" in user_input.lower()):
        ai_message(f"Which method would you like to use for task extraction? Options: {', '.join(TASK_EXTRACTION_METHODS)}.")
        st.session_state.next_action = "choose_task_extraction_method"
    elif st.session_state.next_action == "select_tasks_to_create":
        # Allow user to type 'show tasks' to re-display tasks
        if user_input.strip().lower() in ["show tasks", "show task", "list tasks", "tasks", "show"]:
            if st.session_state.tasks and len(st.session_state.tasks) > 0:
                ai_message("Extracted tasks:")
                if all(isinstance(t, dict) for t in st.session_state.tasks):
                    import pandas as pd
                    df = pd.DataFrame(st.session_state.tasks)
                    if not df.empty:
                        st.table(df)
                    else:
                        st.info("No task information to display.")
                else:
                    for i, t in enumerate(st.session_state.tasks, 1):
                        st.markdown(f"**Task {i}:** {t}")
            else:
                st.info("No tasks to display.")
            ai_message("Please type the task numbers you want to create in Jira (e.g., '1,3'), or 'all' to create all.")
            st.session_state.next_action = "select_tasks_to_create"
        else:
            # Parse user input for task numbers or 'all'
            selected = []
            if user_input.strip().lower() == 'all':
                selected = list(range(len(st.session_state.tasks)))
            else:
                try:
                    selected = [int(x.strip())-1 for x in user_input.split(',') if x.strip().isdigit() and 0 < int(x.strip()) <= len(st.session_state.tasks)]
                except Exception:
                    selected = []
            if not selected:
                ai_message("No valid task numbers selected. Please type the task numbers you want to create in Jira (e.g., '1,3'), or 'all' to create all. Type 'show tasks' to see the list again.")
                st.session_state.next_action = "select_tasks_to_create"
            else:
                ai_message("Creating selected tasks in Jira...")
                print(f"[DEBUG][Jira] Selected task indices: {selected}")
                llm_task_manager = LLMTaskManagerAgent()
                created = []
                for idx in selected:
                    t = st.session_state.tasks[idx]
                    print(f"[DEBUG][Jira] Attempting to create Jira issue for task: {t}")
                    if llm_task_manager.jira:
                        issue_dict = {
                            'project': {'key': llm_task_manager.jira_project},
                            'summary': t.get('title', t.get('Summary', ''))[:255],
                            'description': t.get('description', t.get('Description', f"Auto-created from meeting {st.session_state.meeting_id}")),
                            'issuetype': {'name': 'Task'},
                        }
                        if t.get('owner') or t.get('Assignee'):
                            issue_dict['assignee'] = {'name': t.get('owner', t.get('Assignee'))}
                        if t.get('due') or t.get('Due Date'):
                            issue_dict['duedate'] = t.get('due', t.get('Due Date'))
                        print(f"[DEBUG][Jira] Issue dict: {issue_dict}")
                        try:
                            issue = llm_task_manager.jira.create_issue(fields=issue_dict)
                            print(f"[DEBUG][Jira] Created issue: {issue.key}")
                            t['jira_issue'] = issue.key
                            created.append(issue.key)
                        except Exception as e:
                            print(f"[ERROR][Jira] Exception during issue creation: {e}")
                            t['jira_error'] = str(e)
                    else:
                        print("[ERROR][Jira] Jira connection not configured.")
                        t['jira_error'] = "Jira connection not configured."
                print(f"[DEBUG][Jira] Created issues: {created}")
                if created:
                    ai_message(f"Tasks created in Jira! Issues: {created}")
                else:
                    ai_message("No tasks created in Jira (Jira not configured or error occurred).")
                st.session_state.next_action = None
    elif "summarize" in user_input.lower():
        ai_message("Please paste your meeting transcript or type 'calendar' to fetch events.")
        st.session_state.next_action = "await_transcript"
    elif "extract" in user_input.lower() or "task" in user_input.lower():
        if st.session_state.transcript:
            ai_message(f"Which method would you like to use for task extraction? Options: {', '.join(TASK_EXTRACTION_METHODS)}.")
            st.session_state.next_action = "choose_task_extraction_method"
        else:
            ai_message("Please provide a meeting transcript first (type 'summarize' to start or 'calendar' to fetch events).")
            st.session_state.next_action = None
    elif "jira" in user_input.lower():
        if st.session_state.tasks:
            ai_message("Creating tasks in Jira...")
            llm_task_manager = LLMTaskManagerAgent()
            created = []
            for t in st.session_state.tasks:
                if llm_task_manager.jira:
                    issue_dict = {
                        'project': {'key': llm_task_manager.jira_project},
                        'summary': t.get('title', t.get('Summary', ''))[:255],
                        'description': t.get('description', t.get('Description', f"Auto-created from meeting {st.session_state.meeting_id}")),
                        'issuetype': {'name': 'Task'},
                    }
                    if t.get('owner') or t.get('Assignee'):
                        issue_dict['assignee'] = {'name': t.get('owner', t.get('Assignee'))}
                    if t.get('due') or t.get('Due Date'):
                        issue_dict['duedate'] = t.get('due', t.get('Due Date'))
                    try:
                        issue = llm_task_manager.jira.create_issue(fields=issue_dict)
                        t['jira_issue'] = issue.key
                        created.append(issue.key)
                    except Exception as e:
                        t['jira_error'] = str(e)
            if created:
                ai_message(f"Tasks created in Jira! Issues: {created}")
            else:
                ai_message("No tasks created in Jira (Jira not configured or error occurred).")
        else:
            ai_message("No tasks available to create in Jira. Please extract tasks first.")
        st.session_state.next_action = None
    else:
        ai_message("I can help you summarize meetings, extract tasks (NLP or LLM), fetch calendar events, or create Jira issues. What would you like to do?")
        st.session_state.next_action = None

# Display chat history
for msg in st.session_state.chat_history:
    st.chat_message(msg["role"]).write(msg["content"])
