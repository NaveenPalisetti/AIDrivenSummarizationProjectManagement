from fastapi import FastAPI, Request
from pydantic import BaseModel

app = FastAPI()

class Message(BaseModel):
    type: str
    payload: dict
    metadata: dict = {}

@app.post("/summary")
async def summarize(msg: Message):
    # Dummy summary logic
    summary = f"Summary for: {msg.payload.get('text', '')[:30]}..."
    return {"type": "summary_response", "payload": {"summary": summary}, "metadata": msg.metadata}
