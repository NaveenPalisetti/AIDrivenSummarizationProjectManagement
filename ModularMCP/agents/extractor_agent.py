# Extractor Agent FastAPI Service

from fastapi import FastAPI

app = FastAPI()

@app.get("/extract/")
def extract(transcript_id: str):
    # Dummy extraction logic
    tasks = [f"Task 1 from {transcript_id}", f"Task 2 from {transcript_id}"]
    return {"tasks": tasks}
