# Truth Guardian — Vakratunda
### AI vs AI Scam Detection System
**Meta PyTorch Hackathon x Scaler School of Technology**

## Demo Video
[![Truth Guardian Demo](https://img.youtube.com/vi/eyrkVPflfLI/0.jpg)](https://youtu.be/eyrkVPflfLI)

## What it does
An AI vs AI battle system where:
- **Attacker AI** generates realistic scam messages (bank fraud, OTP tricks, lottery scams)
- **Defender AI** (Truth Guardian) detects and classifies each message in real time

## How it works
- Input: Text message
- Output: SCAM DETECTED / SAFE with confidence score
- Achieves **0.9000+ accuracy** on test set

## HF Space
https://huggingface.co/spaces/Akash154/Truth-Guard

## Tech Stack
- Python 3
- Groq API + LLaMA 3.1 8B
- Gradio
- Keyword-based offline fallback detector
