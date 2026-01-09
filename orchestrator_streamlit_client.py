"""
Streamlit Orchestrator Client: A standalone Streamlit app that sends user queries to the orchestrator API endpoint and displays results.
"""


import streamlit as st
import requests
from mcp.ui.orchestrator_ui_components import (
    event_selector, display_event_details, display_processed_transcripts, display_summaries, display_errors
)

API_URL = "http://localhost:8000/mcp/orchestrate"  # Adjust if your FastAPI server runs elsewhere

st.set_page_config(page_title="AI Orchestrator Client", layout="wide")
st.title("🤖 AI Orchestrator Client")
st.caption("This app sends queries to the orchestrator API and displays the workflow results.")

query = st.text_input("Enter your request (e.g., 'Summarize and create jira'):")
user = st.text_input("User:", value="alice")
date = st.text_input("Date (YYYY-MM-DD):", value="2026-01-09")
permissions = st.text_input("Permissions (comma-separated):", value="summary,jira")
mode = st.selectbox("Summarization Mode", ["auto", "llm", "bart", "mistral"], index=0)
create_jira = st.checkbox("Approve and create Jira tasks after summarization", value=False)


# Step 1: Fetch events and display for selection
if st.button("Fetch Events"):
    st.write(f"[DEBUG] UI sending mode: {mode}")
    payload = {
        "query": query,
        "user": user,
        "date": date if date else None,
        "permissions": [p.strip() for p in permissions.split(",") if p.strip()],
        "mode": mode,
        "create_jira": create_jira
    }
    st.write(f"[DEBUG] UI payload: {payload}")
    try:
        response = requests.post(API_URL, json=payload)
        if response.status_code == 200:
            result = response.json()
            st.session_state['last_result'] = result
        else:
            st.error(f"API Error: {response.status_code} {response.text}")
    except Exception as e:
        st.error(f"Request failed: {e}")

# Step 2: Let user select events and process
result = st.session_state.get('last_result', None)
if result:
    st.subheader("Event Count:")
    st.write(result.get("event_count", 0))
    st.subheader("Transcript Count:")
    st.write(result.get("transcript_count", 0))
    events = result.get("calendar_events", [])
    transcripts = result.get("calendar_transcripts", [])
    # Build event titles for selection
    selected_indices = event_selector(events, transcripts)

    if st.button("Process Selected Events"):
        st.write(f"[DEBUG] UI sending mode: {mode}")
        payload = {
            "query": query,
            "user": user,
            "date": date if date else None,
            "permissions": [p.strip() for p in permissions.split(",") if p.strip()],
            "selected_event_indices": selected_indices,
            "mode": mode,
            "create_jira": create_jira
        }
        st.write(f"[DEBUG] UI payload: {payload}")
        try:
            response = requests.post(API_URL, json=payload)
            if response.status_code == 200:
                result = response.json()
                st.session_state['last_result'] = result
            else:
                st.error(f"API Error: {response.status_code} {response.text}")
        except Exception as e:
            st.error(f"Request failed: {e}")

    # Display selected event details
    display_event_details(events, transcripts, selected_indices)

    # Display processed transcripts
    processed = result.get("processed_transcripts", [])
    display_processed_transcripts(processed)

    # Display summaries
    summaries = result.get("summaries", [])
    # Handle both string and list for backward compatibility
    if isinstance(summaries, str):
        display_summaries([summaries])
    else:
        display_summaries(summaries)

    # Show any errors
    display_errors(result)
