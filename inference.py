import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

ATTACKER_MESSAGES = [
    "Your bank account is suspended. Verify KYC now.",
    "Congratulations! You won a lottery prize of Rs.5,00,000. Share OTP to claim.",
    "URGENT: Your SBI account will be blocked in 24 hours. Call 9876543210.",
    "Your UPI is compromised. Enter MPIN on this link to secure it now.",
    "Income Tax refund of Rs.18,340 pending. Verify PAN on this portal.",
    "Hey, are we still meeting for lunch tomorrow at 1pm?",
    "Happy birthday! Hope you have a wonderful day ahead.",
    "Mom, I'll be home by 9. Please keep dinner ready.",
    "RBI has released a special cash prize. Send Aadhaar to claim.",
    "The cricket match starts at 7pm today. Don't miss it!",
]

GROUND_TRUTH = [True, True, True, True, True, False, False, False, True, False]

def predict(message):
    if not message or len(message.strip()) == 0:
        return {"prediction": "No input", "is_scam": False}

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": f"""Analyze this message. Reply in this exact format:
VERDICT: SCAM or SAFE
CONFIDENCE: 0-100
CATEGORY: urgency/financial/reward/fear/otp/other
REASON: one line

Message: {message}"""}],
        temperature=0.2,
        max_tokens=150,
    )

    raw = response.choices[0].message.content.strip()
    is_scam = "VERDICT: SCAM" in raw.upper()
    return {"prediction": raw, "is_scam": is_scam}

def run_inference():
    task_name = "Vakratunda"
    print(f"[START] task={task_name}", flush=True)

    correct = 0
    steps = len(ATTACKER_MESSAGES)

    for i, message in enumerate(ATTACKER_MESSAGES):
        step_num = i + 1
        result = predict(message)
        expected = GROUND_TRUTH[i]
        is_correct = result["is_scam"] == expected
        reward = 1.0 if is_correct else 0.0
        if is_correct:
            correct += 1
        print(f"[STEP] step={step_num} reward={reward:.4f}", flush=True)

    final_score = correct / steps
    print(f"[END] task={task_name} score={final_score:.4f} steps={steps}", flush=True)

if __name__ == "__main__":
    run_inference()
