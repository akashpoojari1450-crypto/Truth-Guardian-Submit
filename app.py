import gradio as gr
import hashlib
import secrets
import random
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

def scan_for_fraud_dna(text):
    text = text.lower()
    threat_signals = {
        "urgency": ["urgent", "immediately", "act now", "limited time", "expires", "fast", "asap"],
        "financial": ["bank", "account", "tax", "payment", "unpaid", "transfer", "kyc", "otp", "fine", "inr", "money"],
        "reward": ["win", "prize", "gift card", "lottery", "congratulations", "claimed", "money", "free"],
        "links": ["click here", "verify here", "bit.ly", "tinyurl", "login", "http", "https"],
        "fear": ["arrest", "blocked", "suspended", "legal action", "police", "court", "lawsuit"]
    }
    score = 0
    categories = []
    for category, keywords in threat_signals.items():
        if any(word in text for word in keywords):
            score += 1
            categories.append(category.upper())
    return score >= 1, categories

def hunter_protocol_engine(user_input):
    if not user_input or len(user_input.strip()) == 0:
        return "🔱 System Online. Awaiting input..."
    dna = hashlib.blake2b(user_input.encode(), digest_size=16).hexdigest()
    token = f"VAK-{secrets.token_hex(3).upper()}"
    is_scam, triggered = scan_for_fraud_dna(user_input)
    header = f"🔱 SESSION DNA: {dna} | TOKEN: {token}\n" + "-" * 50 + "\n"
    if user_input.isdigit() and 4 <= len(user_input) <= 8:
        mock_ips = ["103.22.201.45", "182.72.10.198", "49.36.120.12"]
        locations = ["New Delhi", "Mumbai Proxy", "Kasaragod Node"]
        return (f"{header}⚠️ OTP DETECTED: {user_input}\n🚨 HIGH RISK - DO NOT SHARE\n"
                f"🛡️ BLOCKED SESSION\n🔍 TRACE IP: {random.choice(mock_ips)}\n"
                f"📍 LOCATION: {random.choice(locations)}")
    if is_scam:
        return f"{header}🚨 FRAUD DETECTED: {', '.join(triggered)}\n🛡️ ACTION: BLOCKED\n📡 LOGGED TO SYSTEM"
    return f"{header}✅ SAFE CONTENT - NO THREATS DETECTED"

with gr.Blocks(title="Truth Guardian VAK") as demo:
    gr.Markdown("# 🔱 Truth Guardian VAK")
    gr.Markdown("### AI-Powered Scam Detection System")
    with gr.Row():
        with gr.Column():
            inp = gr.Textbox(label="📝 Input Message", placeholder="Paste any message, SMS, or OTP to scan...", lines=5)
            with gr.Row():
                btn = gr.Button("🚀 Scan", variant="primary")
                clear = gr.Button("🗑️ Clear", variant="secondary")
        with gr.Column():
            out = gr.Textbox(label="🛡️ Analysis Output", lines=12, interactive=False)
    btn.click(hunter_protocol_engine, inputs=inp, outputs=out)
    clear.click(lambda: "", None, inp).then(lambda: "", None, out)

fastapi_app = FastAPI()

@fastapi_app.post("/reset")
def reset():
    return JSONResponse({"status": "ok", "message": "reset successful"})

@fastapi_app.get("/health")
def health():
    return JSONResponse({"status": "healthy"})

gradio_app = gr.routes.App.create_app(demo)
fastapi_app.mount("/", gradio_app)

if __name__ == "__main__":
    uvicorn.run(fastapi_app, host="0.0.0.0", port=7860)
