# backend/agent/stock_agent.py
import os
import yfinance as yf
from langchain.chat_models import ChatOpenAI

# Use environment variable for safety
OPENAI_API_KEY = "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"
  # or hardcode temporarily

llm = ChatOpenAI(
    model_name="gpt-4o-mini",
    temperature=0.7,
    openai_api_key=OPENAI_API_KEY
)

async def investigate_reason(ticker: str, start_date: str, end_date: str):
    # 1️⃣ Fetch stock data
    df = yf.download(ticker, start=start_date, end=end_date, auto_adjust=True)
    # Optional: summarize price movement
    start_price = df['Close'].iloc[0]
    end_price = df['Close'].iloc[-1]
    movement = "increased" if end_price > start_price else "decreased"

    # 2️⃣ Prepare GPT-4 prompt
    prompt = f"""
    The stock {ticker} from {start_date} to {end_date} {movement}.
    Provide a short explanation why this price changed. Include news, earnings, social media sentiment if relevant.
    Keep it concise for a node label.
    """

    # 3️⃣ Get GPT-4 response
    response = llm.generate([{"role": "user", "content": prompt}])
    reason = response.generations[0].text.strip()

    # 4️⃣ Return structured data
    return {
        "start_price": start_price,
        "end_price": end_price,
        "movement": movement,
        "gpt_reason": reason
    }
