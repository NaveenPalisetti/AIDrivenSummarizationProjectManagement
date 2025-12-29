# Risk Agent FastAPI Service

from fastapi import FastAPI

app = FastAPI()

@app.get("/risk/")
def detect_risk(transcript_id: str):
    # Dummy risk detection logic
    risks = [f"Risk detected in {transcript_id}"]
    return {"risks": risks}
