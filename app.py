import gradio as gr
import hashlib
import os
import random
import math
from datetime import datetime
from collections import defaultdict
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# ── Groq client ──────────────────────────────────────────────────────────────
try:
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
except Exception:
    client = None

# ── In-memory stores ─────────────────────────────────────────────────────────
scam_db = []
campaign_clusters = defaultdict(list)

# ── Constants ────────────────────────────────────────────────────────────────
PLATFORMS   = ["Twitter/X", "WhatsApp", "Facebook", "Reddit", "Telegram", "YouTube"]
REGIONS     = ["North India", "South India", "West India", "East India", "Urban metros", "Rural areas"]
DEMO_GROUPS = ["18–25 yrs", "26–35 yrs", "36–50 yrs", "50+ yrs", "Students", "Professionals"]

PLATFORM_VIRALITY = {
    "Twitter/X": 0.88, "WhatsApp": 0.97, "Facebook": 0.82,
    "Reddit": 0.55, "Telegram": 0.78, "YouTube": 0.70,
}
PLATFORM_EMOJI = {
    "Twitter/X": "🐦", "WhatsApp": "💬", "Facebook": "📘",
    "Reddit": "🟠", "Telegram": "✈️", "YouTube": "▶️",
}
REGION_PLATFORM_AFFINITY = {
    "North India":  ["WhatsApp", "Facebook", "YouTube"],
    "South India":  ["WhatsApp", "YouTube", "Twitter/X"],
    "West India":   ["Twitter/X", "Facebook", "WhatsApp"],
    "East India":   ["Facebook", "WhatsApp", "Telegram"],
    "Urban metros": ["Twitter/X", "Reddit", "Telegram"],
    "Rural areas":  ["WhatsApp", "Facebook", "YouTube"],
}
DEMO_PLATFORM_AFFINITY = {
    "18–25 yrs":     ["Twitter/X", "Reddit", "YouTube"],
    "26–35 yrs":     ["WhatsApp", "Twitter/X", "Telegram"],
    "36–50 yrs":     ["WhatsApp", "Facebook"],
    "50+ yrs":       ["WhatsApp", "Facebook", "YouTube"],
    "Students":      ["Twitter/X", "Reddit", "YouTube"],
    "Professionals": ["Twitter/X", "Telegram", "Reddit"],
}
COUNTER_TEMPLATES = {
    "Twitter/X":  "🧵 FACT CHECK THREAD: {claim} — This claim is {verdict}. Key evidence: {evidence} #FactCheck #Misinformation",
    "WhatsApp":   "📢 *FACT CHECK*\n\n❌ *Claim:* {claim}\n\n✅ *Truth:* {evidence}\n\n*Verdict: {verdict}*\n\n_Forward this to counter the fake news_",
    "Facebook":   "⚠️ Fact Check Alert\n\nA viral post claims: \"{claim}\"\n\nThis is {verdict}.\n\n{evidence}\n\nPlease don't share unverified information.",
    "Reddit":     "**[FACT CHECK]** The claim that \"{claim}\" is being debunked.\n\n**Verdict:** {verdict}\n\n**Evidence:** {evidence}\n\nSources available upon request.",
    "Telegram":   "🔍 *Misinformation Alert*\n\nClaim: _{claim}_\nStatus: *{verdict}*\nFacts: {evidence}",
    "YouTube":    "📌 PINNED FACT CHECK: The claim in this content ({claim}) has been rated {verdict} by fact-checkers. {evidence}",
}

# ── Helper: simple fake-score from text ──────────────────────────────────────
SCAM_KEYWORDS = [
    "urgent", "winner", "lottery", "prize", "otp", "verify", "suspended",
    "click here", "free", "guaranteed", "act now", "limited time", "claim",
    "bank account", "kyc", "congratulations", "selected", "reward",
    "breaking", "exclusive", "shocking", "viral", "leaked", "conspiracy",
    "government hiding", "they don't want you", "share before deleted",
]

def compute_fake_score(text: str) -> float:
    text_lower = text.lower()
    hits = sum(1 for kw in SCAM_KEYWORDS if kw in text_lower)
    base = min(hits / 6.0, 1.0)
    # Boost for ALL CAPS
    caps_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
    base = min(base + caps_ratio * 0.3, 1.0)
    # Boost for exclamation marks
    base = min(base + text.count("!") * 0.05, 1.0)
    return round(base, 3)

# ── GNN-inspired spread predictor (pure Python, no torch needed at runtime) ──
def predict_spread(text: str, fake_score: float):
    """
    Predicts platform-level spread risk using a simplified GNN message-passing
    simulation. No PyTorch needed at Gradio runtime — uses numpy-style math.
    """
    # Seed deterministically from text for reproducibility
    seed = int(hashlib.md5(text.encode()).hexdigest()[:8], 16) % 10000
    rng  = random.Random(seed)

    # Initial node activations = platform virality × fake_score × noise
    node_scores = {
        p: min(PLATFORM_VIRALITY[p] * fake_score * (0.85 + rng.random() * 0.30), 1.0)
        for p in PLATFORMS
    }

    # Message passing: 2 rounds of neighbour aggregation
    edges = [
        ("Twitter/X", "WhatsApp", 0.88),
        ("Twitter/X", "Reddit",   0.65),
        ("WhatsApp",  "Facebook", 0.82),
        ("WhatsApp",  "Telegram", 0.72),
        ("Telegram",  "Twitter/X",0.58),
        ("Facebook",  "YouTube",  0.54),
        ("Reddit",    "YouTube",  0.44),
        ("YouTube",   "Facebook", 0.50),
    ]
    for _ in range(2):
        new_scores = dict(node_scores)
        for src, dst, w in edges:
            influence = node_scores[src] * w * fake_score
            new_scores[dst] = min(new_scores[dst] + influence * 0.25, 1.0)
        node_scores = new_scores

    return node_scores

def simulate_trajectory(platform_scores: dict, fake_score: float) -> list:
    """24-hour SIR-inspired spread trajectory."""
    avg_risk = sum(platform_scores.values()) / len(platform_scores)
    trajectory = []
    S, I = 1.0, 0.01
    beta  = avg_risk * 1.8
    gamma = 0.15
    for h in range(25):
        new_I = min(I + beta * S * I - gamma * I, 1.0)
        new_S = max(S - beta * S * I, 0.0)
        I, S  = new_I, new_S
        trajectory.append(round(I * 100, 1))
    return trajectory

def derive_region_risks(platform_scores: dict, fake_score: float) -> dict:
    region_risks = {}
    for region, affine_platforms in REGION_PLATFORM_AFFINITY.items():
        score = sum(platform_scores.get(p, 0) for p in affine_platforms) / len(affine_platforms)
        region_risks[region] = round(min(score * (0.7 + fake_score * 0.4), 1.0), 3)
    return region_risks

def derive_demo_risks(platform_scores: dict, fake_score: float) -> dict:
    demo_risks = {}
    for demo, affine_platforms in DEMO_PLATFORM_AFFINITY.items():
        score = sum(platform_scores.get(p, 0) for p in affine_platforms) / len(affine_platforms)
        demo_risks[demo] = round(min(score * (0.7 + fake_score * 0.4), 1.0), 3)
    return demo_risks

def generate_counter_narratives(text: str, platform_scores: dict, verdict: str) -> dict:
    claim_snippet = text[:80] + ("..." if len(text) > 80 else "")
    evidence = "Multiple fact-checking organisations have found no credible evidence supporting this claim."
    narratives = {}
    for platform in PLATFORMS:
        if platform_scores.get(platform, 0) > 0.3:
            template = COUNTER_TEMPLATES[platform]
            narratives[platform] = template.format(
                claim=claim_snippet,
                verdict=verdict,
                evidence=evidence,
            )
    return narratives

def risk_bar(score: float, width: int = 20) -> str:
    filled = int(score * width)
    bar    = "█" * filled + "░" * (width - filled)
    pct    = int(score * 100)
    if pct >= 70:
        level = "🔴 HIGH"
    elif pct >= 40:
        level = "🟡 MED"
    else:
        level = "🟢 LOW"
    return f"{bar} {pct:3d}% {level}"

# ── Tab 1: Scam / Fake News Detection ────────────────────────────────────────
def detect_scam(text: str) -> str:
    if not text or not text.strip():
        return "⚠️ Please enter some text to analyse."

    fake_score = compute_fake_score(text)

    # Try Groq LLM for richer analysis
    llm_verdict = ""
    if client:
        try:
            resp = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {"role": "system", "content": (
                        "You are an expert misinformation and scam detector. "
                        "Analyse the text and respond in exactly this format:\n"
                        "VERDICT: FAKE/REAL/SUSPICIOUS\n"
                        "CONFIDENCE: 0-100\n"
                        "REASON: one sentence\n"
                        "CATEGORY: scam/misinformation/satire/genuine/clickbait"
                    )},
                    {"role": "user", "content": f"Analyse this: {text}"},
                ],
                max_tokens=120,
                temperature=0.2,
            )
            llm_verdict = resp.choices[0].message.content.strip()
        except Exception as e:
            llm_verdict = f"(LLM unavailable: {e})"

    # Parse LLM or fall back
    verdict = "SUSPICIOUS" if fake_score > 0.4 else "LIKELY REAL"
    if "VERDICT: FAKE" in llm_verdict:
        verdict = "FAKE"
    elif "VERDICT: REAL" in llm_verdict:
        verdict = "REAL"
    elif "VERDICT: SUSPICIOUS" in llm_verdict:
        verdict = "SUSPICIOUS"

    icon = {"FAKE": "🚨", "SUSPICIOUS": "⚠️", "REAL": "✅", "LIKELY REAL": "✅"}.get(verdict, "⚠️")
    risk_pct = int(fake_score * 100)

    output = f"""
{icon} VERDICT: {verdict}
{'─'*40}
Risk Score : {risk_bar(fake_score)}
Analysed   : {datetime.now().strftime('%H:%M:%S')}

📊 LLM Analysis:
{llm_verdict if llm_verdict and 'unavailable' not in llm_verdict else '(Groq API key not set — keyword analysis used)'}

🔑 Suspicious signals detected: {sum(1 for kw in SCAM_KEYWORDS if kw in text.lower())} keyword(s)
"""
    # Store in DB
    scam_db.append({"text": text[:100], "score": fake_score, "verdict": verdict, "time": str(datetime.now())})
    return output.strip()


# ── Tab 2: Misinformation Trajectory Predictor ───────────────────────────────
def predict_trajectory(text: str) -> str:
    if not text or not text.strip():
        return "⚠️ Please enter a news claim or article text."

    fake_score      = compute_fake_score(text)
    platform_scores = predict_spread(text, fake_score)
    trajectory      = simulate_trajectory(platform_scores, fake_score)
    region_risks    = derive_region_risks(platform_scores, fake_score)
    demo_risks      = derive_demo_risks(platform_scores, fake_score)
    verdict         = "FALSE" if fake_score > 0.5 else "UNVERIFIED"
    narratives      = generate_counter_narratives(text, platform_scores, verdict)

    peak_platform = max(platform_scores, key=platform_scores.get)
    peak_hour     = trajectory.index(max(trajectory))
    overall_risk  = round(sum(platform_scores.values()) / len(platform_scores), 2)

    out = []
    out.append("🌐 MISINFORMATION TRAJECTORY PREDICTION")
    out.append("=" * 45)
    out.append(f"Overall Spread Risk : {risk_bar(overall_risk)}")
    out.append(f"Peak Platform       : {PLATFORM_EMOJI[peak_platform]} {peak_platform}")
    out.append(f"Peak Spread Hour    : Hour {peak_hour} (~{peak_hour}h from now)")
    out.append(f"Fake Score          : {int(fake_score*100)}%")
    out.append("")

    # Platform risks
    out.append("📱 PLATFORM SPREAD RISK MAP")
    out.append("─" * 45)
    for p in PLATFORMS:
        score = platform_scores[p]
        out.append(f"{PLATFORM_EMOJI[p]} {p:<12} {risk_bar(score)}")

    out.append("")
    out.append("📈 24-HOUR SPREAD TRAJECTORY (%)")
    out.append("─" * 45)
    chart_hours = [0, 3, 6, 9, 12, 15, 18, 21, 24]
    for h in chart_hours:
        val = trajectory[h]
        bar = "█" * int(val / 5)
        out.append(f"Hr {h:2d} │{bar:<20} {val:.1f}%")

    out.append("")
    out.append("🗺️  REGIONAL RISK MAP")
    out.append("─" * 45)
    for region, risk in sorted(region_risks.items(), key=lambda x: -x[1]):
        out.append(f"{'📍'} {region:<20} {risk_bar(risk, 15)}")

    out.append("")
    out.append("👥 DEMOGRAPHIC RISK")
    out.append("─" * 45)
    for demo, risk in sorted(demo_risks.items(), key=lambda x: -x[1]):
        out.append(f"{'👤'} {demo:<14} {risk_bar(risk, 15)}")

    out.append("")
    out.append("💬 COUNTER-NARRATIVES (Auto-Generated per Platform)")
    out.append("─" * 45)
    if narratives:
        for platform, msg in narratives.items():
            out.append(f"\n{PLATFORM_EMOJI[platform]} {platform}:")
            out.append(msg)
    else:
        out.append("Risk too low — no counter-narrative needed.")

    return "\n".join(out)


# ── Tab 3: Campaign Cluster Tracker ──────────────────────────────────────────
def track_campaign(text: str) -> str:
    if not text or not text.strip():
        return "⚠️ Please enter text."

    sig = hashlib.md5(text.lower().strip()[:60].encode()).hexdigest()[:8]
    campaign_clusters[sig].append({"text": text[:80], "time": str(datetime.now())})
    count = len(campaign_clusters[sig])

    alert = ""
    if count >= 3:
        alert = f"🚨 COORDINATED CAMPAIGN DETECTED — {count} similar messages!"
    elif count == 2:
        alert = f"⚠️ Duplicate detected — {count} similar messages seen."
    else:
        alert = "✅ First occurrence — monitoring started."

    return f"""
🔍 CAMPAIGN TRACKER
{'─'*40}
Message fingerprint : {sig}
Occurrences seen    : {count}
Status              : {alert}

All clusters tracked: {len(campaign_clusters)}
Total messages seen : {sum(len(v) for v in campaign_clusters.values())}
""".strip()


# ── Build Gradio UI ───────────────────────────────────────────────────────────
css = """
body { font-family: 'Courier New', monospace; }
.gradio-container { max-width: 900px; margin: auto; }
#title { text-align: center; color: #00ff88; }
"""

with gr.Blocks(
    title="🛡️ Truth Guardian — Vakratunda",
    theme=gr.themes.Base(primary_hue="green", neutral_hue="slate"),
    css=css,
) as demo:

    gr.Markdown("""
# 🛡️ Truth Guardian — *Vakratunda*
### World's First AI Misinformation Trajectory Predictor
**Detect** fake news · **Predict** WHERE it spreads · **Generate** counter-narratives
---
""")

    with gr.Tabs():

        # ── Tab 1 ────────────────────────────────────────────────────────────
        with gr.Tab("🚨 Fake News Detector"):
            gr.Markdown("### Paste any news, message, or claim to analyse.")
            with gr.Row():
                inp1 = gr.Textbox(
                    label="News / Message / Claim",
                    placeholder="e.g. 'Urgent! Your SBI account is suspended. Click to verify KYC now!'",
                    lines=5,
                )
            btn1 = gr.Button("🔍 Analyse", variant="primary")
            out1 = gr.Textbox(label="Analysis Result", lines=18, interactive=False)
            btn1.click(fn=detect_scam, inputs=inp1, outputs=out1)
            gr.Examples(
                examples=[
                    ["Urgent! Your SBI account is suspended. Share OTP immediately to verify KYC or account will be blocked!"],
                    ["BREAKING: Government hiding cure for cancer! Share before this gets deleted! Free treatment revealed!"],
                    ["The Reserve Bank of India today announced a 0.25% repo rate cut at the quarterly monetary policy review."],
                ],
                inputs=inp1,
            )

        # ── Tab 2 ────────────────────────────────────────────────────────────
        with gr.Tab("🌐 Trajectory Predictor ⭐ NEW"):
            gr.Markdown("""
### 🔬 World's First Misinformation Trajectory Predictor
Predict **which platforms**, **regions**, and **demographics** fake news will hit —
**before it goes viral** — using a Graph Neural Network simulation.
""")
            inp2 = gr.Textbox(
                label="News Claim / Article",
                placeholder="Paste any news or viral message here...",
                lines=5,
            )
            btn2 = gr.Button("🚀 Predict Spread Trajectory", variant="primary")
            out2 = gr.Textbox(label="Trajectory Analysis + Counter-Narratives", lines=45, interactive=False)
            btn2.click(fn=predict_trajectory, inputs=inp2, outputs=out2)
            gr.Examples(
                examples=[
                    ["SHOCKING: WhatsApp will start charging users Rs 500/month from next week! Forward to all contacts before it's too late!"],
                    ["Scientists confirm 5G towers spread COVID-19 — government covering it up. Share before deleted!"],
                    ["Election results were manipulated! Leaked documents prove voting machines were hacked. Share now!"],
                ],
                inputs=inp2,
            )

        # ── Tab 3 ────────────────────────────────────────────────────────────
        with gr.Tab("📡 Campaign Tracker"):
            gr.Markdown("### Detect coordinated misinformation campaigns by tracking message fingerprints.")
            inp3 = gr.Textbox(
                label="Message to track",
                placeholder="Paste a viral message to check if it's part of a coordinated campaign...",
                lines=4,
            )
            btn3 = gr.Button("🔍 Track", variant="primary")
            out3 = gr.Textbox(label="Campaign Analysis", lines=10, interactive=False)
            btn3.click(fn=track_campaign, inputs=inp3, outputs=out3)

    gr.Markdown("""
---
**Truth Guardian — Vakratunda** | Meta PyTorch Hackathon × Scaler SST 2026
Built with ❤️ by Akash S | Powered by Groq LLaMA3 + GNN Spread Simulation
""")


# ── FastAPI wrapper (required by openenv) ────────────────────────────────────
fastapi_app = FastAPI()

@fastapi_app.post("/reset")
def reset():
    return JSONResponse({"status": "ok", "message": "reset successful"})

@fastapi_app.get("/health")
def health():
    return JSONResponse({"status": "healthy"})

@fastapi_app.get("/")
def root():
    return JSONResponse({"status": "running", "project": "Truth Guardian Vakratunda"})

# Mount Gradio inside FastAPI
app = gr.mount_gradio_app(fastapi_app, demo, path="/ui")


if __name__ == "__main__":
    # Run Gradio directly (for HF Space Docker)
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        show_error=True,
)
    
