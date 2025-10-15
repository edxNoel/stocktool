from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf
import os
from openai import AsyncOpenAI

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.post("/")
async def analyze_stock(request: Request):
    try:
        req = await request.json()
        ticker = req.get("ticker")
        start_date = req.get("start_date")
        end_date = req.get("end_date")

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

        ai_analysis = await call_gpt(f"Analyze {ticker}:\n{summary_text}")

        return {"status": "success", "ticker": ticker, "summary": rounded, "ai_analysis": ai_analysis}
    except Exception as e:
        return {"status": "error", "message": str(e)}
