import requests
import pandas as pd
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from binance_api import fetch_24hr_ticker

def get_top_n_pairs_by_volatility(n=10, tf="15m"):
    try:
        tickers = fetch_24hr_ticker()
        fut = [t for t in tickers if t["symbol"].endswith("USDT") and ("PERP" not in t)]
        df = pd.DataFrame(fut)
        df["priceChangePercent"] = df["priceChangePercent"].astype(float)
        df["abs_change"] = df["priceChangePercent"].abs()
        top = df.sort_values("abs_change", ascending=False).head(n)
        return top["symbol"].tolist()
    except Exception:
        return ["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT"][:n]

def send_telegram_message(text: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        return r.status_code == 200
    except Exception:
        return False
