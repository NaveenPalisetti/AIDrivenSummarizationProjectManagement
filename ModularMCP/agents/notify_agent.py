from fastapi import FastAPI, Request
from pydantic import BaseModel

app = FastAPI()

class Message(BaseModel):
    type: str
    payload: dict
    metadata: dict = {}

@app.post("/notify")
async def notify(msg: Message):
    # Dummy notify logic
    notification = f"Notification sent: {msg.payload.get('message', '')}"
    return {"type": "notify_response", "payload": {"notification": notification}, "metadata": msg.metadata}
