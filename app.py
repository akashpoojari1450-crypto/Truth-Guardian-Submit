import gradio as gr
import hashlib
import secrets
import random
import os
import anthropic
from datetime import datetime
from collections import defaultdict
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn
from dotenv import load_dotenv

load_dotenv()

# ============================================
# ANTHROPIC CLIENT
# ============================================
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# ============================================
# SCAM DNA DATABASE
# ============================================
scam_db = []
campaign_clusters = defaultdict(list)
honeytrap_db = []

def get_scam_dna(text):
    return hashlib.blake2b(text.lower().strip().encode(), digest_size=8).hexdigest()

def get_campaign_dna(text):
    words = sorted(set(text.lower().split()))[:10]
    return hashlib.md5(" ".join(words).encode()).hexdigest()[:8]

# ============================================
# AI SCAM DETECTOR
# ============================================
def ai_detect_scam(message):
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        messages=[{
            "role": "user",
            "content": f"""You are a scam detection expert. Analyze this message and respond in exactly this format:
VERDICT: SCAM or SAFE
CONFIDENCE: 0-100
CATEGORY: (urgency/financial/reward/fear/otp/other)
REASON: (one line explanation)

Message: {message}"""
        }]
    )
    return response.content[0].text

# ============================================
# AI HONEYTRAP GENERATOR
# ============================================
def ai_generate_honeytrap(scam_message):
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=300,
        messages=[{
            "role": "user",
            "content": f"""You are a cybersecurity honeytrap system. 
A scammer sent this message: "{scam_message}"

Generate a fake but convincing reply that:
1. Makes the scammer think they succeeded
2. Contains FAKE details (fake account numbers, fake OTPs, fake names)
3. Will waste the scammer's time
4. Is short and realistic

Reply with ONLY the fake response message, nothing else."""
        }]
    )
    return response.content[0].text

# ============================================
# AI SCAMMER (for AI vs AI battle)
# ============================================
def ai_generate_scam(category):
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=200,
        messages=[{
            "role": "user",
            "content": f"""You are simulating a scammer for cybersecurity training only.
Generate a realistic {category} scam SMS message that a scammer might send in India.
Keep it under 3 sentences. Make it sound urgent and real.
Reply with ONLY the scam message."""
        }]
    )
    return response.content[0].text

# ============================================
# MAIN SCAN ENGINE
# ============================================
def full_scan(message):
    if not message or len(message.strip()) == 0:
        return "⏳ Awaiting input...", "", ""

    dna = get_scam_dna(message)
    campaign_id = get_campaign_dna(message)

    # AI Detection
    ai_result = ai_detect_scam(message)
    is_scam = "VERDICT: SCAM" in ai_result

    # Store
    entry = {
        "dna": dna,
        "campaign_id": campaign_id,
        "is_scam": is_scam,
        "message": message[:100],
        "timestamp": datetime.now().isoformat()
    }
    scam_db.append(entry)
    campaign_clusters[campaign_id].append(dna)
    campaign_count = len(campaign_clusters[campaign_id])

    # Build result
    header = f"🧬 DNA: {dna} | CAMPAIGN: {campaign_id}\n" + "="*50 + "\n"
    if campaign_count > 1:
        header += f"🚨 CAMPAIGN ALERT: {campaign_count} messages from same gang!\n"

    result = header + ai_result

    # Honeytrap
    honeytrap = ""
    if is_scam:
        honeytrap = ai_generate_honeytrap(message)
        honeytrap_db.append({"scam": message[:100], "trap": honeytrap, "time": datetime.now().isoformat()})

    # Dashboard
    total = len(scam_db)
    scams = sum(1 for s in scam_db if s["is_scam"])
    dashboard = f"""📊 LIVE INTELLIGENCE DASHBOARD
{'='*40}
📥 Total Scans      : {total}
🚨 Scams Detected   : {scams} ({int(scams/total*100) if total else 0}%)
🍯 Honeytraps Set   : {len(honeytrap_db)}
🧬 Campaigns Tracked: {len(campaign_clusters)}
{'='*40}"""

    return result, f"🍯 HONEYTRAP REPLY:\n{honeytrap}" if honeytrap else "✅ Safe — no honeytrap needed", dashboard

# ============================================
# AI VS AI BATTLE
# ============================================
def ai_battle(category):
    scam = ai_generate_scam(category)
    detection = ai_detect_scam(scam)
    is_caught = "VERDICT: SCAM" in detection
    
    result = f"""⚔️ AI VS AI BATTLE
{'='*50}
🔴 SCAMMER AI GENERATED:
{scam}

🔵 DETECTOR AI RESPONDED:
{detection}

{'='*50}
{'✅ DETECTOR WINS — Scam caught!' if is_caught else '❌ SCAMMER WINS — Evaded detection!'}"""
    return result

# ============================================
# GRADIO UI
# ============================================
with gr.Blocks(title="Truth Guardian VAK ∞", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🔱 Truth Guardian VAK — World's First AI Scam Firewall")
    gr.Markdown("### AI Detection + Honeytrap System + AI vs AI Battle Arena")
    gr.Markdown("---")

    with gr.Tabs():
        # Tab 1: Scan
        with gr.Tab("🛡️ Scan & Honeytrap"):
            gr.Markdown("Paste any suspicious message — AI detects it and generates a honeytrap reply to send back to the scammer")
            with gr.Row():
                with gr.Column():
                    inp = gr.Textbox(label="📝 Suspicious Message", placeholder="Paste SMS, WhatsApp message, or OTP request...", lines=5)
                    with gr.Row():
                        btn = gr.Button("🚀 Scan + Generate Honeytrap", variant="primary")
                        clear = gr.Button("🗑️ Clear", variant="secondary")
                with gr.Column():
                    out = gr.Textbox(label="🛡️ AI Detection Result", lines=8, interactive=False)
            honeytrap_out = gr.Textbox(label="🍯 Honeytrap Reply (Send this back to scammer!)", lines=5, interactive=False)
            dashboard = gr.Textbox(label="📊 Live Dashboard", lines=8, interactive=False)
            btn.click(full_scan, inputs=inp, outputs=[out, honeytrap_out, dashboard])
            clear.click(lambda: ("", "", ""), None, [inp, out, honeytrap_out])

        # Tab 2: AI vs AI
        with gr.Tab("⚔️ AI vs AI Battle"):
            gr.Markdown("Watch Scammer AI fight Detector AI in real time!")
            category = gr.Dropdown(
                choices=["bank fraud", "KYC scam", "lottery win", "job offer", "OTP theft", "legal threat"],
                label="⚔️ Choose Scam Category",
                value="bank fraud"
            )
            battle_btn = gr.Button("⚔️ Start Battle!", variant="primary")
            battle_out = gr.Textbox(label="🥊 Battle Result", lines=15, interactive=False)
            battle_btn.click(ai_battle, inputs=category, outputs=battle_out)

# ============================================
# FASTAPI
# ============================================
fastapi_app = FastAPI()

@fastapi_app.post("/reset")
def reset():
    return JSONResponse({"status": "ok"})

@fastapi_app.get("/health")
def health():
    return JSONResponse({"status": "healthy"})

demo.queue()
gradio_app = gr.mount_gradio_app(fastapi_app, demo, path="/")
app = fastapi_app

if __name__ == "__main__":
    uvicorn.run(fastapi_app, host="0.0.0.0", port=7860)
