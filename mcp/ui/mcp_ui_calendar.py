"""
Streamlit UI: Google Calendar Event Transcript Summarization
"""
import streamlit as st
from mcp.tools.mcp_calendar_tool import get_calendar_transcripts

st.header("Google Calendar Event Transcript Summarization")

# User input for date range
days_back = st.number_input("Days back to fetch events", min_value=1, max_value=30, value=7)
days_forward = st.number_input("Days forward to fetch events", min_value=0, max_value=30, value=1)
calendar_id = st.text_input("Google Calendar ID", value="primary")

if st.button("Fetch Event Transcripts"):
    with st.spinner("Fetching transcripts from Google Calendar..."):
        transcripts = get_calendar_transcripts(days_back=days_back, days_forward=days_forward, calendar_id=calendar_id)
    if transcripts:
        st.success(f"Found {len(transcripts)} event transcripts.")
        for i, t in enumerate(transcripts, 1):
            st.subheader(f"Event {i} Transcript")
            st.text_area(f"Transcript {i}", t, height=200)
    else:
        st.warning("No transcripts found for the selected range.")
