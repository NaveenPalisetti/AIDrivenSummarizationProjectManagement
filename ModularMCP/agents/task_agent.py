from fastapi import FastAPI, Request
from pydantic import BaseModel

app = FastAPI()

class Message(BaseModel):
    type: str
    payload: dict
    metadata: dict = {}

@app.post("/task")
async def task(msg: Message):
    # Dummy task logic
    result = {"status": "task created", "task": msg.payload.get('task', 'No task')}
    return {"type": "task_response", "payload": result, "metadata": msg.metadata}
