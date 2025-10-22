# utils/data.py
"""
Data processing utilities
"""
import pandas as pd
from api.binance import fetch_24hr_ticker


def get_top_n_pairs_by_volatility(n=10, tf="15m"):
    # Use 24h tickers: fallback choose top movers by priceChangePercent magnitude
    try:
        tickers = fetch_24hr_ticker()
        # Filter perpetual futures symbols (USDT perpetual)
        fut = [t for t in tickers if t["symbol"].endswith("USDT") and ("PERP" not in t)]  # filtering heuristic
        df = pd.DataFrame(fut)
        df["priceChangePercent"] = df["priceChangePercent"].astype(float)
        df["abs_change"] = df["priceChangePercent"].abs()
        top = df.sort_values("abs_change", ascending=False).head(n)
        return top["symbol"].tolist()
    except Exception:
        # fallback list
        return ["BTCUSDT", "ETHUSDT", "XRPUSDT", "BNBUSDT", "SOLUSDT", "LINKUSDT", "ADAUSDT", "DOGEUSDT", "LTCUSDT", "MATICUSDT"][:n]
