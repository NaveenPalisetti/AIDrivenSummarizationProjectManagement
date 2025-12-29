# Summarizer Agent FastAPI Service

from fastapi import FastAPI
from typing import Optional

app = FastAPI()

# Dummy in-memory storage for demonstration
summaries = {}

@app.get("/summarize/")
def summarize(transcript_id: str):
    # In a real system, fetch transcript and generate summary
    # Here, just return a dummy summary
    summary = f"Summary for transcript {transcript_id}"
    summaries[transcript_id] = summary
    return {"summary": summary}
