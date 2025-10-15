# backend/main.py
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf
import asyncio
from openai import AsyncOpenAI
import numpy as np

# Detect whether running in Vercel
IS_VERCEL = bool(os.getenv("VERCEL"))

fastapi_app = FastAPI(title="AI Stock Analyzer")
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Use Socket.IO only in local dev (not in serverless)
if not IS_VERCEL:
    import socketio
    sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
    app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app)
else:
    sio = None
    app = fastapi_app

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def call_gpt(prompt: str) -> str:
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an AI stock summarizer."},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"GPT call error: {str(e)}"

@fastapi_app.post("/analyze")
async def analyze_stock(request: Request):
    try:
        req = await request.json()
        ticker = req.get("ticker")
        start_date = req.get("start_date")
        end_date = req.get("end_date")

        if sio:
            await sio.emit("node_update", {"label": f"Fetching {ticker}..."})

        df = yf.download(ticker, start=start_date, end=end_date)
        if df.empty:
            return {"status": "error", "message": "No data found"}

        summary = {
            "Start Price": df["Close"].iloc[0],
            "End Price": df["Close"].iloc[-1],
            "High": df["High"].max(),
            "Low": df["Low"].min(),
            "Mean Volume": df["Volume"].mean(),
            "Price Change (%)": ((df["Close"].iloc[-1] - df["Close"].iloc[0]) / df["Close"].iloc[0]) * 100,
        }

        rounded = {k: round(float(v), 2) for k, v in summary.items()}
        summary_text = "\n".join([f"{k}: {v}" for k, v in rounded.items()])

        prompt = f"Analyze {ticker}:\n{summary_text}"
        ai_analysis = await call_gpt(prompt)

        return {"status": "success", "ticker": ticker, "summary": rounded, "ai_analysis": ai_analysis}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}

if not IS_VERCEL:
    @sio.event
    async def connect(sid, environ):
        print(f"Client connected: {sid}")

    @sio.event
    async def disconnect(sid):
        print(f"Client disconnected: {sid}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000)
