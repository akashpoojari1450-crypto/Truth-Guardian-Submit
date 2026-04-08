import gradio as gr
import hashlib
import secrets
import random
import json
import os
from datetime import datetime
from collections import defaultdict
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

# ============================================
# SCAM DNA DATABASE (in-memory)
# ============================================
scam_db = []
campaign_clusters = defaultdict(list)

def scan_for_fraud_dna(text):
    text_lower = text.lower()
    threat_signals = {
        "urgency": ["urgent", "immediately", "act now", "limited time", "expires", "asap"],
        "financial": ["bank", "account", "tax", "payment", "unpaid", "transfer", "kyc", "otp", "fine", "money"],
        "reward": ["win", "prize", "gift card", "lottery", "congratulations", "free"],
        "links": ["click here", "verify here", "bit.ly", "tinyurl", "login"],
        "otp": ["otp", "one time password", "verification code", "do not share"],
    }
    
    score = 0
    triggered = []
    for category, keywords in threat_signals.items():
        for kw in keywords:
            if kw in text_lower:
                score += 1
                triggered.append(f"{category}:{kw}")
    
    if score == 0:
        verdict = "✅ SAFE"
        risk = "Low"
    elif score <= 2:
        verdict = "⚠️ SUSPICIOUS"
        risk = "Medium"
    else:
        verdict = "🚨 SCAM DETECTED"
        risk = "High"
    
    dna = hashlib.md5(text_lower.encode()).hexdigest()[:12]
    
    entry = {
        "id": secrets.token_hex(4),
        "text": text[:100],
        "verdict": verdict,
        "risk": risk,
        "score": score,
        "signals": triggered,
        "dna": dna,
        "timestamp": datetime.now().strftime("%H:%M:%S")
    }
    scam_db.append(entry)
    
    result = f"**Verdict:** {verdict}\n"
    result += f"**Risk Level:** {risk}\n"
    result += f"**Threat Score:** {score}\n"
    result += f"**Scam DNA:** `{dna}`\n"
    if triggered:
        result += f"**Signals:** {', '.join(triggered)}\n"
    
    return result

def get_dashboard():
    total = len(scam_db)
    if total == 0:
        return "No scans yet. Try scanning some text!"
    scams = sum(1 for x in scam_db if "SCAM" in x["verdict"])
    suspicious = sum(1 for x in scam_db if "SUSPICIOUS" in x["verdict"])
    safe = sum(1 for x in scam_db if "SAFE" in x["verdict"])
    
    dash = f"**📊 Dashboard**\n\n"
    dash += f"Total Scans: {total}\n"
    dash += f"🚨 Scams: {scams}\n"
    dash += f"⚠️ Suspicious: {suspicious}\n"
    dash += f"✅ Safe: {safe}\n\n"
    dash += "**Recent Scans:**\n"
    for entry in scam_db[-5:][::-1]:
        dash += f"- [{entry['timestamp']}] {entry['verdict']} | DNA:`{entry['dna']}`\n"
    return dash

with gr.Blocks(title="Truth Guardian VAK") as demo:
    gr.Markdown("# 🛡️ Truth Guardian VAK\n**AI Scam Detection & Campaign Fingerprinting**")
    with gr.Row():
        with gr.Column():
            text_input = gr.Textbox(label="Enter text to scan", lines=4, placeholder="Paste suspicious message here...")
            scan_btn = gr.Button("🔍 Scan for Scams", variant="primary")
            result_output = gr.Markdown(label="Result")
        with gr.Column():
            dash_btn = gr.Button("📊 Refresh Dashboard")
            dash_output = gr.Markdown()
    
    scan_btn.click(scan_for_fraud_dna, inputs=text_input, outputs=result_output)
    dash_btn.click(get_dashboard, outputs=dash_output)

fastapi_app = FastAPI(title="Truth Guardian API")

@fastapi_app.post("/reset")
def reset():
    global scam_db, campaign_clusters
    scam_db = []
    campaign_clusters = defaultdict(list)
    return JSONResponse({"status": "ok", "message": "Environment reset successfully"})

@fastapi_app.get("/health")
def health():
    return JSONResponse({"status": "healthy", "service": "Truth Guardian VAK"})

@fastapi_app.get("/info")
def info():
    return JSONResponse({"name": "Truth Guardian VAK", "version": "1.0.0"})

app = gr.mount_gradio_app(fastapi_app, demo, path="/")

def main():
    uvicorn.run(app, host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()
