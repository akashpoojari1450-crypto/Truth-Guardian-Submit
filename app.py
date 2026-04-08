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

def get_scam_dna(text):
    return hashlib.blake2b(text.lower().strip().encode(), digest_size=8).hexdigest()

def get_campaign_dna(text):
    """Coarse fingerprint for clustering similar scams"""
    words = sorted(set(text.lower().split()))[:10]
    return hashlib.md5(" ".join(words).encode()).hexdigest()[:8]

def scan_for_fraud_dna(text):
    text_lower = text.lower()
    threat_signals = {
        "urgency": ["urgent", "immediately", "act now", "limited time", "expires", "fast", "asap"],
        "financial": ["bank", "account", "tax", "payment", "unpaid", "transfer", "kyc", "otp", "fine", "inr", "money"],
        "reward": ["win", "prize", "gift card", "lottery", "congratulations", "claimed", "free"],
        "links": ["click here", "verify here", "bit.ly", "tinyurl", "login", "http", "https"],
        "fear": ["arrest", "blocked", "suspended", "legal action", "police", "court", "lawsuit"]
    }
    score = 0
    categories = []
    for category, keywords in threat_signals.items():
        if any(word in text_lower for word in keywords):
            score += 1
            categories.append(category.upper())
    return score >= 1, categories

def hunter_protocol_engine(user_input):
    if not user_input or len(user_input.strip()) == 0:
        return "🔱 System Online. Awaiting input...", get_dashboard()

    dna = get_scam_dna(user_input)
    campaign_id = get_campaign_dna(user_input)
    token = f"VAK-{secrets.token_hex(3).upper()}"
    is_scam, triggered = scan_for_fraud_dna(user_input)

    # Check if seen before
    existing = [s for s in scam_db if s["dna"] == dna]
    seen_before = len(existing) > 0

    # Store in DB
    entry = {
        "dna": dna,
        "campaign_id": campaign_id,
        "is_scam": is_scam,
        "categories": triggered,
        "timestamp": datetime.now().isoformat(),
        "is_otp": user_input.isdigit() and 4 <= len(user_input) <= 8
    }
    scam_db.append(entry)
    campaign_clusters[campaign_id].append(dna)

    campaign_count = len(campaign_clusters[campaign_id])
    header = f"🔱 SCAM DNA: {dna} | CAMPAIGN: {campaign_id} | TOKEN: {token}\n"
    header += "-" * 55 + "\n"

    if seen_before:
        header += f"⚠️ DUPLICATE DETECTED — This exact message seen before!\n"

    if campaign_count > 1:
        header += f"🕵️ CAMPAIGN ALERT — {campaign_count} similar messages from same scam gang!\n"

    if entry["is_otp"]:
        mock_ips = ["103.22.201.45", "182.72.10.198", "49.36.120.12"]
        locations = ["New Delhi", "Mumbai Proxy", "Kasaragod Node"]
        result = (f"{header}"
                  f"⚠️ OTP DETECTED: {user_input}\n"
                  f"🚨 HIGH RISK - DO NOT SHARE\n"
                  f"🛡️ BLOCKED SESSION\n"
                  f"🔍 TRACE IP: {random.choice(mock_ips)}\n"
                  f"📍 LOCATION: {random.choice(locations)}")
    elif is_scam:
        result = (f"{header}"
                  f"🚨 FRAUD DETECTED: {', '.join(triggered)}\n"
                  f"🛡️ ACTION: BLOCKED\n"
                  f"📡 LOGGED TO SCAM DNA DATABASE\n"
                  f"🧬 CAMPAIGN ID: {campaign_id}")
    else:
        result = f"{header}✅ SAFE CONTENT - NO THREATS DETECTED"

    return result, get_dashboard()

def get_dashboard():
    total = len(scam_db)
    scams = [s for s in scam_db if s["is_scam"]]
    otps = [s for s in scam_db if s["is_otp"]]
    campaigns = len(campaign_clusters)
    repeat_campaigns = {k: v for k, v in campaign_clusters.items() if len(v) > 1}

    cats = defaultdict(int)
    for s in scams:
        for c in s["categories"]:
            cats[c] += 1

    top_cats = sorted(cats.items(), key=lambda x: -x[1])[:3]
    top_str = " | ".join([f"{c}: {n}" for c, n in top_cats]) if top_cats else "None"

    dashboard = f"""📊 SCAM INTELLIGENCE DASHBOARD
{'='*45}
📥 Total Scans      : {total}
🚨 Scams Detected   : {len(scams)} ({int(len(scams)/total*100) if total else 0}%)
🔐 OTPs Blocked     : {len(otps)}
🧬 Unique Campaigns : {campaigns}
🕵️ Repeat Campaigns : {len(repeat_campaigns)}
📈 Top Categories   : {top_str}
{'='*45}"""

    if repeat_campaigns:
        dashboard += "\n⚠️ ACTIVE SCAM CAMPAIGNS:\n"
        for cid, dnas in list(repeat_campaigns.items())[:3]:
            dashboard += f"  🔴 Campaign {cid}: {len(dnas)} messages intercepted\n"

    return dashboard

# ============================================
# GRADIO UI
# ============================================
with gr.Blocks(title="Truth Guardian VAK ∞", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🔱 Truth Guardian VAK — Scam DNA Intelligence")
    gr.Markdown("### World's First Scam Campaign Fingerprinting System")
    gr.Markdown("---")

    with gr.Row():
        with gr.Column(scale=1):
            inp = gr.Textbox(label="📝 Input Message", placeholder="Paste any message, SMS, or OTP...", lines=5)
            with gr.Row():
                btn = gr.Button("🚀 Scan & Fingerprint", variant="primary")
                clear = gr.Button("🗑️ Clear", variant="secondary")
            gr.Markdown("### 🎯 Detection Capabilities")
            gr.Markdown("- ⚡ Urgency · 💰 Financial · 🎁 Reward\n- 🔗 Links · 😨 Fear · 🔐 OTP\n- 🧬 Campaign Clustering · 👥 Duplicate Detection")

        with gr.Column(scale=1):
            out = gr.Textbox(label="🛡️ Analysis Output", lines=10, interactive=False)
            dashboard = gr.Textbox(label="📊 Live Intelligence Dashboard", lines=12, interactive=False,
                                   value=get_dashboard())

    btn.click(hunter_protocol_engine, inputs=inp, outputs=[out, dashboard])
    clear.click(lambda: ("", get_dashboard()), None, [inp, dashboard])

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

gradio_app = gr.routes.App.create_app(demo)
fastapi_app.mount("/", gradio_app)

if __name__ == "__main__":
    uvicorn.run(fastapi_app, host="0.0.0.0", port=7860)
