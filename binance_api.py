import requests
import pandas as pd

BINANCE_FUTURES_BASE = "https://fapi.binance.com"

def fetch_exchange_info():
    r = requests.get(BINANCE_FUTURES_BASE + "/fapi/v1/exchangeInfo", timeout=10)
    r.raise_for_status()
    return r.json()

def fetch_24hr_ticker():
    r = requests.get(BINANCE_FUTURES_BASE + "/fapi/v1/ticker/24hr", timeout=10)
    r.raise_for_status()
    return r.json()

def fetch_klines(symbol: str, interval: str = "15m", limit: int = 500):
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    r = requests.get(BINANCE_FUTURES_BASE + "/fapi/v1/klines", params=params, timeout=10)
    r.raise_for_status()
    data = r.json()
    df = pd.DataFrame(data, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "num_trades",
        "taker_buy_base", "taker_buy_quote", "ignore"
    ])
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    numeric_cols = ["open", "high", "low", "close", "volume", "taker_buy_base", "taker_buy_quote"]
    df[numeric_cols] = df[numeric_cols].astype(float)
    return df

def fetch_funding_rate(symbol: str, limit: int = 1):
    params = {"symbol": symbol, "limit": limit}
    r = requests.get(BINANCE_FUTURES_BASE + "/fapi/v1/fundingRate", params=params, timeout=10)
    r.raise_for_status()
    arr = r.json()
    return float(arr[-1]["fundingRate"]) if arr else 0.0

def fetch_open_interest(symbol: str):
    params = {"symbol": symbol}
    r = requests.get(BINANCE_FUTURES_BASE + "/fapi/v1/openInterest", params=params, timeout=10)
    r.raise_for_status()
    return float(r.json().get("openInterest", 0.0))

def fetch_agg_trades(symbol: str, start_time_ms: int = None, limit: int = 1000):
    params = {"symbol": symbol, "limit": limit}
    if start_time_ms:
        params["startTime"] = start_time_ms
    r = requests.get(BINANCE_FUTURES_BASE.replace("fapi", "api") + "/v3/aggTrades", params=params, timeout=10)
    r.raise_for_status()
    return r.json()
