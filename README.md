---
title: Truth Guardian VAK
emoji: 🛡️
colorFrom: blue
colorTo: purple
sdk: docker
app_file: app.py
pinned: false
---

# Truth Guardian VAK - Scam Detection System

## Features
- Real-time scam detection
- OTP theft prevention
- Session tracking with DNA tokens
- FastAPI + Gradio integration

## Test Examples
- `123456` → OTP detected
- `Your bank account is suspended` → Scam detected
- `Hello` → Safe

## API Endpoints
- `POST /reset` - Reset environment
- `GET /health` - Health check
- `GET /info` - Service info
