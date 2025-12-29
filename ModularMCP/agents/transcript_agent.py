# Transcript Agent FastAPI Service

from fastapi import FastAPI, Request
import uuid

app = FastAPI()

transcripts = {}

@app.post("/transcript/")
async def store_transcript(request: Request):
    data = await request.json()
    transcript_id = str(uuid.uuid4())
    transcripts[transcript_id] = data["transcript"]
    return {"transcript_id": transcript_id}
