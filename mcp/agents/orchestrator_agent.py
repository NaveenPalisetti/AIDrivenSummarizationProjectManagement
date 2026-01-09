"""
Orchestrator agent for MCP: Handles user queries, input validation, agent routing, parallel execution, and workflow state management.
"""
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed

from mcp.protocols.a2a import a2a_endpoint, a2a_request
from mcp.agents.mcp_google_calendar import MCPGoogleCalendar
from mcp.agents.transcript_preprocessing_agent import TranscriptPreprocessingAgent
from mcp.agents.summarization_agent import SummarizationAgent

class OrchestratorState:
    def __init__(self):
        self.state = {}
    def update(self, key, value):
        self.state[key] = value
    def get(self, key, default=None):
        return self.state.get(key, default)


class OrchestratorAgent:
    def __init__(self):
        pass  # No state needed for single-agent workflow

    @a2a_endpoint
    def handle_query(self, query: str, user: str, date: str = None, permissions: list = None, selected_event_indices: list = None, mode: str = None, create_jira: bool = False) -> dict:
        print(f"[DEBUG] OrchestratorAgent.handle_query received mode: {mode}, create_jira: {create_jira}")
        mode = "bart"  # Force BART mode regardless of input
        # Validate inputs
        if not query or not user:
            return {"error": "Missing query or user."}
        result = {}
        try:
            cal = MCPGoogleCalendar(calendar_id="primary")
            import datetime
            now = datetime.datetime.utcnow()
            start_time = now - datetime.timedelta(days=37)
            end_time = now + datetime.timedelta(days=1)
            events = cal.fetch_events(start_time, end_time)
            transcripts = cal.get_transcripts_from_events(events)
            result['calendar_events'] = events
            result['calendar_transcripts'] = transcripts
            result['event_count'] = len(events)
            result['transcript_count'] = len(transcripts)

            # UI-driven event selection
            if selected_event_indices is not None and isinstance(selected_event_indices, list) and selected_event_indices:
                # Only process selected events/transcripts
                selected_events = [events[i] for i in selected_event_indices if 0 <= i < len(events)]
                selected_transcripts = [transcripts[i] for i in selected_event_indices if 0 <= i < len(transcripts)]
            else:
                selected_events = events
                selected_transcripts = transcripts
            result['selected_events'] = selected_events
            result['selected_transcripts'] = selected_transcripts
            result['selected_event_indices'] = selected_event_indices

            # Step 2: Transcript Preprocessing Agent (protocol-driven)
            preproc = TranscriptPreprocessingAgent()
            preproc_payload = {"transcripts": selected_transcripts}
            preproc_response = a2a_request(preproc.process, preproc_payload)
            if preproc_response["status"] == "ok":
                processed_transcripts = preproc_response["result"]
                result['processed_transcripts'] = processed_transcripts
                result['processed_transcript_count'] = len(processed_transcripts)

                # Step 3: Summarization Agent (protocol-driven)
                print(f"[DEBUG] Passing mode to SummarizationAgent: {mode}")
                summarizer = SummarizationAgent(mode=mode)
                summarization_payload = {"processed_transcripts": processed_transcripts, "mode": mode}
                summarization_response = a2a_request(summarizer.summarize_protocol, summarization_payload)
                if summarization_response["status"] == "ok":
                    summaries = summarization_response["result"]
                    result['summaries'] = summaries
                    result['summary_count'] = len(summaries) if isinstance(summaries, list) else 1
                    # Step 4: Jira Agent (protocol-driven, only if approved)
                    if create_jira:
                        print("[DEBUG] Passing summary to JiraAgent (approved by UI)")
                        from mcp.agents.jira_agent import JiraAgent
                        jira_agent = JiraAgent()
                        jira_payload = {"summary": summaries, "user": user, "date": date}
                        jira_response = a2a_request(jira_agent.create_jira, jira_payload)
                        if jira_response["status"] == "ok":
                            result['jira'] = jira_response["result"]
                        else:
                            result['jira_error'] = jira_response["error"]
                    else:
                        print("[DEBUG] Jira creation not approved by UI; skipping JiraAgent call.")
                else:
                    result['summarization_error'] = summarization_response["error"]
            else:
                result['preprocessing_error'] = preproc_response["error"]
        except Exception as e:
            result['calendar_error'] = str(e)
        return result

    def _validate_date(self, date: str) -> bool:
        # Simple YYYY-MM-DD check
        import re
        return bool(re.match(r"^\\d{4}-\\d{2}-\\d{2}$", date))

    def _check_permissions(self, user: str, permissions: List[str]) -> bool:
        # Stub: always true for demo
        return True

    def _detect_intent(self, query: str) -> str:
        # Simple keyword-based intent detection
        q = query.lower()
        if "calendar" in q or "event" in q or "fetch transcript" in q:
            return "calendar"
        if "summary" in q:
            return "summarize"
        if "jira" in q:
            return "create_jira"
        return "unknown"

    def _route_agents(self, intent: str) -> List[str]:
        # Map intent to agent function names
        if intent == "calendar":
            return ["calendar_agent"]
        if intent == "summarize":
            return ["summary_agent"]
        if intent == "create_jira":
            return ["jira_agent"]
        if intent == "unknown":
            return ["summary_agent", "jira_agent"]  # Example: run both
        return []

    def _execute_agents_parallel(self, agents: List[str], query: str, user: str, date: str):
        # Map agent names to callables
        def calendar_agent_func(**kwargs):
            import traceback
            debug_info = {}
            try:
                # Fetch events for the last 7 days and next 1 day
                cal = MCPGoogleCalendar()
                import datetime
                now = datetime.datetime.utcnow()
                start_time = now - datetime.timedelta(days=7)
                end_time = now + datetime.timedelta(days=1)
                debug_info['start_time'] = str(start_time)
                debug_info['end_time'] = str(end_time)
                events = cal.fetch_events(start_time, end_time)
                debug_info['event_count'] = len(events)
                transcripts = cal.get_transcripts_from_events(events)
                debug_info['transcript_count'] = len(transcripts)
                return {"transcripts": transcripts, "event_count": len(events), "debug": debug_info}
            except Exception as e:
                debug_info['error'] = str(e)
                debug_info['traceback'] = traceback.format_exc()
                return {"error": str(e), "debug": debug_info}

        agent_funcs = {
            "calendar_agent": calendar_agent_func,
            "summary_agent": lambda **kwargs: {"summary": f"Summary for {kwargs['query']}"},
            "jira_agent": lambda **kwargs: {"jira": f"Jira created for {kwargs['query']}"}
        }
        results = {}
        with ThreadPoolExecutor() as executor:
            futures = {executor.submit(a2a_request, agent_funcs[a], {"query": query, "user": user, "date": date}): a for a in agents}
            for future in as_completed(futures):
                agent = futures[future]
                try:
                    results[agent] = future.result()
                except Exception as e:
                    results[agent] = {"error": str(e)}
        return results

# Example usage:
# orchestrator = OrchestratorAgent()
# result = orchestrator.handle_query("Please summarize and create jira", "alice", date="2026-01-09", permissions=["summary", "jira"])
# print(result)
