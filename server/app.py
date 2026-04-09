from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI()

def predict(message):
    if not message or len(message.strip()) == 0:
        return {"prediction": "No input", "is_scam": False}
    scam_keywords = [
        "otp", "bank", "suspend", "verify", "kyc", "urgent", "lottery",
        "prize", "won", "claim", "password", "mpin", "upi", "aadhaar",
        "pan", "refund", "blocked", "click", "link", "legal", "action"
    ]
    matches = [kw for kw in scam_keywords if kw in message.lower()]
    is_scam = len(matches) >= 2
    if message.strip().isdigit() and 4 <= len(message.strip()) <= 8:
        return {"prediction": "OTP DETECTED", "is_scam": True}
    return {"prediction": "SCAM DETECTED" if is_scam else "SAFE", "is_scam": is_scam}

@app.post("/reset")
def reset():
    return JSONResponse({"status": "ok", "message": "reset successful"})

@app.get("/")
def root():
    return {"status": "running", "project": "Truth Guardian Vakratunda"}

@app.post("/predict")
def predict_endpoint(data: dict):
    result = predict(data.get("message", ""))
    return JSONResponse(result)

def serve():
    uvicorn.run(app, host="0.0.0.0", port=7860)
