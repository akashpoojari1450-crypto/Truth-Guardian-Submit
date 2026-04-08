import os
import gradio as gr

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:7860")
MODEL_NAME = os.environ.get("MODEL_NAME", "truth-guardian-vak")
HF_TOKEN = os.environ.get("HF_TOKEN", None)

def predict(message):
    """Scam detection prediction function"""
    if not message or len(message.strip()) == 0:
        return {
            "prediction": "No input provided",
            "is_scam": False,
            "confidence": 0.0
        }
    
    # Scam keywords
    scam_keywords = [
        "bank", "account", "otp", "password", "pin", "verification",
        "lottery", "prize", "winner", "won", "gift", "free",
        "urgent", "immediately", "act now", "asap",
        "suspend", "block", "arrest", "legal", "court", "police"
    ]
    
    message_lower = message.lower()
    detected_keywords = [kw for kw in scam_keywords if kw in message_lower]
    is_scam = len(detected_keywords) > 0
    
    # Special OTP detection (4-8 digits)
    if message.isdigit() and 4 <= len(message) <= 8:
        return {
            "prediction": "OTP DETECTED - HIGH RISK",
            "is_scam": True,
            "confidence": 0.95,
            "category": "OTP_THEFT"
        }
    
    if is_scam:
        return {
            "prediction": "FRAUD DETECTED",
            "is_scam": True,
            "confidence": 0.85,
            "category": "SCAM_ATTEMPT",
            "detected_keywords": detected_keywords
        }
    
    return {
        "prediction": "SAFE CONTENT",
        "is_scam": False,
        "confidence": 0.90,
        "category": "SAFE"
    }

# Create Gradio interface
app = gr.Interface(
    fn=predict,
    inputs=gr.Textbox(
        label="Enter Message to Scan",
        placeholder="Paste any suspicious message, SMS, or OTP here...",
        lines=4
    ),
    outputs=gr.JSON(label="Analysis Result"),
    title="🔱 Truth Guardian VAK",
    description="Real-time scam detection system",
    theme="soft"
)

if __name__ == "__main__":
    app.launch()
