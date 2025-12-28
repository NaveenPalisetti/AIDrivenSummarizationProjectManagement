from mcp.agents.meeting_followup_agent import MeetingFollowupAgent

def check_and_create_followup_meeting(transcript, calendar_id='primary'):
    agent = MeetingFollowupAgent(calendar_id=calendar_id)
    result = agent.create_followup_event(transcript)
    return result
