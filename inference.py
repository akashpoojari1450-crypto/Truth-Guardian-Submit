import os
import gradio as gr

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:7860")
MODEL_NAME = os.environ.get("MODEL_NAME", "truth-guardian-vak")
HF_TOKEN = os.environ.get("HF_TOKEN", None)

def predict(message):
    if not message or len(message.strip()) == 0:
        return {"prediction": "No input", "is_scam": False}
    
    scam_keywords = ["bank", "otp", "password", "lottery", "prize", "urgent", "verify"]
    is_scam = any(kw in message.lower() for kw in scam_keywords)
    
    if message.isdigit() and 4 <= len(message) <= 8:
        return {"prediction": "OTP DETECTED", "is_scam": True}
    if is_scam:
        return {"prediction": "FRAUD DETECTED", "is_scam": True}
    return {"prediction": "SAFE", "is_scam": False}

app = gr.Interface(
    fn=predict,
    inputs=gr.Textbox(label="Enter message"),
    outputs=gr.JSON(label="Result"),
    title="Truth Guardian VAK"
)
