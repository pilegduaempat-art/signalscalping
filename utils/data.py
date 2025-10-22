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
        # Filter out delisted or problematic pairs
        excluded_symbols = ['COCOSUSDT', 'BEAMUSDT']  # Add problematic symbols here
        
        fut = [t for t in tickers 
               if t["symbol"].endswith("USDT") 
               and "PERP" not in t["symbol"]
               and t["symbol"] not in excluded_symbols
               and float(t.get("volume", 0)) > 0  # Only pairs with volume
        ]
        
        df = pd.DataFrame(fut)
        
        if df.empty:
            return get_fallback_pairs(n)
        
        df["priceChangePercent"] = df["priceChangePercent"].astype(float)
        df["volume"] = df["volume"].astype(float)
        df["abs_change"] = df["priceChangePercent"].abs()
        
        # Sort by volatility and volume
        df = df.sort_values(["abs_change", "volume"], ascending=[False, False])
        top = df.head(n * 2)  # Get 2x to have backup if some fail
        
        return top["symbol"].head(n).tolist()
    except Exception as e:
        print(f"Error in get_top_n_pairs_by_volatility: {e}")
        return get_fallback_pairs(n)


def get_fallback_pairs(n=10):
    """Fallback list of reliable pairs"""
    reliable_pairs = [
        "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "SOLUSDT",
        "ADAUSDT", "DOGEUSDT", "AVAXUSDT", "DOTUSDT", "MATICUSDT"
    ]
    return reliable_pairs[:n]
