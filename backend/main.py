# main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf
import socketio
import asyncio
from openai import AsyncOpenAI
import numpy as np

# ----------------------------
# 1️⃣ FastAPI app
# ----------------------------
fastapi_app = FastAPI()

# Enable CORS
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development, allow all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# 2️⃣ Socket.IO server
# ----------------------------
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app)

# ----------------------------
# 3️⃣ OpenAI client (async)
# ----------------------------
# Hardcoded API key here
client = AsyncOpenAI(api_key="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")

async def call_gpt(prompt: str) -> str:
    """Call GPT asynchronously and return text output."""
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an AI financial data summarizer. "
                        "You describe patterns, volatility, and momentum clearly, "
                        "but never offer investment advice."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.6,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"GPT call error: {str(e)}"

# ----------------------------
# 4️⃣ FastAPI route: /analyze
# ----------------------------
@fastapi_app.post("/analyze")
async def analyze_stock(request: Request):
    try:
        req = await request.json()
        ticker = req.get("ticker")
        start_date = req.get("start_date")
        end_date = req.get("end_date")

        await sio.emit("node_update", {"label": f"Fetching {ticker} price data..."})

        # Fetch stock data
        try:
            df = yf.download(ticker, start=start_date, end=end_date)
        except Exception as e:
            return {"status": "error", "message": f"YFinance error: {str(e)}"}

        if df.empty:
            await sio.emit("node_update", {"label": f"No data found for {ticker}."})
            return {"status": "error", "message": "No data found"}

        # Summarize stock data
        summary = {
            "Start Price": df["Close"].iloc[0],
            "End Price": df["Close"].iloc[-1],
            "High": df["High"].max(),
            "Low": df["Low"].min(),
            "Mean Volume": df["Volume"].mean(),
            "Price Change (%)": (
                (df["Close"].iloc[-1] - df["Close"].iloc[0]) / df["Close"].iloc[0]
            ) * 100,
        }

        # Round summary values for frontend
        rounded_summary = {
            k: round(float(v), 2) if np.isscalar(v) else str(v)
            for k, v in summary.items()
        }

        # Prepare summary text for AI
        summary_text = "\n".join([f"{k}: {v}" for k, v in rounded_summary.items()])

        # --------------------
        # 1️⃣ AI Analysis Node
        # --------------------
        await sio.emit("node_update", {"label": "AI analyzing stock trends..."})
        prompt_analysis = f"""
        Stock data summary for {ticker} ({start_date} → {end_date}):

        {summary_text}

        Describe the overall trend, notable volatility, and general investor sentiment.
        """
        ai_analysis = await call_gpt(prompt_analysis)
        await sio.emit("node_update", {"label": f"AI Analysis: {ai_analysis}"})

        # --------------------
        # 2️⃣ Decision Reasoning Node
        # --------------------
        await sio.emit("node_update", {"label": "AI reasoning about next steps..."})
        prompt_decision = f"""
        Based on the summary and AI analysis for {ticker},
        what might a financial analyst hypothetically infer about market behavior or momentum?
        Provide reasoning without giving buy/sell recommendations.
        """
        decision = await call_gpt(prompt_decision)
        await sio.emit("node_update", {"label": f"Analyst Reasoning: {decision}"})

        # --------------------
        # 3️⃣ Sub-Investigation Node
        # --------------------
        await sio.emit("node_update", {"label": "Exploring further investigation areas..."})
        prompt_sub = f"""
        Given {ticker}'s performance, what external factors
        (e.g., earnings, macro events, sector shifts, sentiment data)
        would be worth exploring to understand movement better?
        """
        sub_investigation = await call_gpt(prompt_sub)
        await sio.emit("node_update", {"label": f"Sub-Investigation: {sub_investigation}"})

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

# ----------------------------
# 5️⃣ Socket.IO events
# ----------------------------
@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")
    await sio.emit("node_update", {"label": "AI Agent Connected"}, to=sid)

@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")
