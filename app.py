import gradio as gr
import hashlib
import secrets
import random
import os
from datetime import datetime
from collections import defaultdict
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

scam_db = []
campaign_clusters = defaultdict(list)
honeytrap_db = []

def get_scam_dna(text):
    return hashlib.blake2b(text.lower().strip().encode(), digest_size=8).hexdigest()

def get_campaign_dna(text):
    words = sorted(set(text.lower().split()))[:10]
    return hashlib.md5(" ".join(words).encode()).hexdigest()[:8]

def ai_call(prompt):
    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500
    )
    return response.choices[0].message.content

def ai_detect_scam(message):
    return ai_call(f"""You are a scam detection expert. Analyze this message and respond in exactly this format:
VERDICT: SCAM or SAFE
CONFIDENCE: 0-100
CATEGORY: (urgency/financial/reward/fear/otp/other)
REASON: (one line explanation)

Message: {message}""")

def ai_generate_honeytrap(scam_message):
    return ai_call(f"""You are a cybersecurity honeytrap system.
A scammer sent: "{scam_message}"
Generate a fake but convincing reply with FAKE details (fake account numbers, fake OTPs, fake names) to waste the scammer's time.
Reply with ONLY the fake response, nothing else.""")

def ai_generate_scam(category):
    return ai_call(f"""Simulate a {category} scam SMS for cybersecurity training in India. Keep it under 3 sentences. Reply with ONLY the scam message.""")

def full_scan(message):
    if not message or len(message.strip()) == 0:
        return "⏳ Awaiting input...", "", ""

    dna = get_scam_dna(message)
    campaign_id = get_campaign_dna(message)
    ai_result = ai_detect_scam(message)
    is_scam = "VERDICT: SCAM" in ai_result

    entry = {"dna": dna, "campaign_id": campaign_id, "is_scam": is_scam, "timestamp": datetime.now().isoformat()}
    scam_db.append(entry)
    campaign_clusters[campaign_id].append(dna)
    campaign_count = len(campaign_clusters[campaign_id])

    header = f"🧬 DNA: {dna} | CAMPAIGN: {campaign_id}\n" + "="*50 + "\n"
    if campaign_count > 1:
        header += f"🚨 CAMPAIGN ALERT: {campaign_count} messages from same gang!\n"

    result = header + ai_result
    honeytrap = ""
    if is_scam:
        honeytrap = ai_generate_honeytrap(message)
        honeytrap_db.append({"scam": message[:100], "trap": honeytrap})

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

def ai_battle(category):
    scam = ai_generate_scam(category)
    detection = ai_detect_scam(scam)
    is_caught = "VERDICT: SCAM" in detection
    return f"""⚔️ AI VS AI BATTLE
{'='*50}
🔴 SCAMMER AI GENERATED:
{scam}

🔵 DETECTOR AI RESPONDED:
{detection}

{'='*50}
{'✅ DETECTOR WINS — Scam caught!' if is_caught else '❌ SCAMMER WINS — Evaded detection!'}"""

with gr.Blocks(title="Truth Guardian VAK ∞", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🔱 Truth Guardian VAK — World's First AI Scam Firewall")
    gr.Markdown("### AI Detection + Honeytrap System + AI vs AI Battle Arena")
    gr.Markdown("---")

    with gr.Tabs():
        with gr.Tab("🛡️ Scan & Honeytrap"):
            gr.Markdown("Paste any suspicious message — AI detects it and generates a honeytrap reply")
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

        with gr.Tab("⚔️ AI vs AI Battle"):
            gr.Markdown("### Watch Scammer AI fight Detector AI in real time!")
            category = gr.Dropdown(
                choices=["bank fraud", "KYC scam", "lottery win", "job offer", "OTP theft", "legal threat"],
                label="Choose Scam Category",
                value="bank fraud"
            )
            battle_btn = gr.Button("⚔️ Start Battle!", variant="primary")
            battle_out = gr.Textbox(label="🥊 Battle Result", lines=15, interactive=False)
            battle_btn.click(ai_battle, inputs=category, outputs=battle_out)

fastapi_app = FastAPI()

@fastapi_app.post("/reset")
def reset():
    return JSONResponse({"status": "ok"})

@fastapi_app.get("/health")
def health():
    return JSONResponse({"status": "healthy"})

demo.queue()
app = gr.mount_gradio_app(fastapi_app, demo, path="/")

if __name__ == "__main__":
    uvicorn.run(fastapi_app, host="0.0.0.0", port=7860)
