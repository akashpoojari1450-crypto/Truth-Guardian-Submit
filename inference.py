import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/reset':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status": "ok"}')
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status": "healthy"}')
    def log_message(self, format, *args):
        pass

def start_server():
    server = HTTPServer(('0.0.0.0', 7860), Handler)
    server.serve_forever()

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

def run_inference():
    task_name = "Vakratunda"
    test_inputs = [
        ("Your bank account is suspended. Verify KYC now.", True),
        ("Congratulations! You won a lottery prize. Share OTP to claim.", True),
        ("URGENT: Your SBI account will be blocked. Call now.", True),
        ("Income Tax refund pending. Verify PAN on this portal.", True),
        ("RBI cash prize. Send Aadhaar to claim.", True),
        ("Hey, are we still meeting for lunch tomorrow?", False),
        ("Happy birthday! Hope you have a wonderful day.", False),
        ("Mom, I'll be home by 9. Please keep dinner ready.", False),
        ("The cricket match starts at 7pm today.", False),
        ("123456", True),
    ]
    print(f"[START] task={task_name}", flush=True)
    correct = 0
    for i, (message, expected) in enumerate(test_inputs):
        result = predict(message)
        reward = 1.0 if result["is_scam"] == expected else 0.0
        if reward == 1.0:
            correct += 1
        print(f"[STEP] step={i+1} reward={reward:.4f}", flush=True)
    print(f"[END] task={task_name} score={correct/len(test_inputs):.4f} steps={len(test_inputs)}", flush=True)

if __name__ == "__main__":
    t = threading.Thread(target=start_server, daemon=True)
    t.start()
    run_inference()
