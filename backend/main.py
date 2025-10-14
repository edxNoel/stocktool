# main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf
import socketio
import asyncio
from openai import AsyncOpenAI
import numpy as np
import os

# FastAPI app
fastapi_app = FastAPI()
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Socket.IO server
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app)

# OpenAI client
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

async def call_gpt(prompt: str) -> str:
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an AI financial data summarizer. Describe trends clearly, do not give financial advice."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.6,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"GPT call error: {str(e)}"

# /analyze route
@fastapi_app.post("/analyze")
async def analyze_stock(request: Request):
    try:
        req = await request.json()
        ticker = req.get("ticker")
        start_date = req.get("start_date")
        end_date = req.get("end_date")

        await sio.emit("node_update", {"label": f"Fetching {ticker} price data..."})

        df = yf.download(ticker, start=start_date, end=end_date)
        if df.empty:
            await sio.emit("node_update", {"label": f"No data found for {ticker}."})
            return {"status": "error", "message": "No data found"}

        summary = {
            "Start Price": df["Close"].iloc[0],
            "End Price": df["Close"].iloc[-1],
            "High": df["High"].max(),
            "Low": df["Low"].min(),
            "Mean Volume": df["Volume"].mean(),
            "Price Change (%)": ((df["Close"].iloc[-1] - df["Close"].iloc[0]) / df["Close"].iloc[0]) * 100,
        }

        rounded_summary = {k: round(float(v), 2) if np.isscalar(v) else str(v) for k, v in summary.items()}
        summary_text = "\n".join([f"{k}: {v}" for k, v in rounded_summary.items()])

        # AI analysis
        await sio.emit("node_update", {"label": "AI analyzing stock trends..."})
        ai_analysis = await call_gpt(f"Stock summary for {ticker}:\n{summary_text}")

        await sio.emit("node_update", {"label": "AI reasoning about next steps..."})
        decision = await call_gpt(f"Based on the summary above for {ticker}, what might a financial analyst infer about market behavior or momentum?")

        await sio.emit("node_update", {"label": "Exploring further investigation areas..."})
        sub_investigation = await call_gpt(f"Given {ticker}'s performance, what external factors would be worth exploring?")

        return {
            "status": "success",
            "ticker": ticker,
            "rows_fetched": len(df),
            "summary": rounded_summary,
            "ai_analysis": ai_analysis,
            "decision": decision,
            "sub_investigation": sub_investigation,
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}

# Socket.IO events
@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")
    await sio.emit("node_update", {"label": "AI Agent Connected"}, to=sid)

@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")

# Entry point for Render
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, log_level="info")

