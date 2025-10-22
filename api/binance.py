# api/binance.py
"""
Binance Futures API calls
"""
import requests
import pandas as pd
import time
from config import BINANCE_FUTURES_BASE


# Rate limiting
LAST_REQUEST_TIME = {}
MIN_REQUEST_INTERVAL = 0.2  # 200ms between requests


def rate_limited_request(url, params=None, timeout=10):
    """
    Make a rate-limited request to avoid 451 errors
    """
    global LAST_REQUEST_TIME
    
    # Wait if needed
    now = time.time()
    if url in LAST_REQUEST_TIME:
        elapsed = now - LAST_REQUEST_TIME[url]
        if elapsed < MIN_REQUEST_INTERVAL:
            time.sleep(MIN_REQUEST_INTERVAL - elapsed)
    
    # Make request with retry
    max_retries = 3
    for attempt in range(max_retries):
        try:
            r = requests.get(url, params=params, timeout=timeout)
            LAST_REQUEST_TIME[url] = time.time()
            
            if r.status_code == 451:
                # Wait longer on 451 error
                wait_time = (attempt + 1) * 2
                time.sleep(wait_time)
                continue
            
            r.raise_for_status()
            return r
        except requests.exceptions.HTTPError as e:
            if attempt == max_retries - 1:
                raise
            time.sleep((attempt + 1) * 1)
    
    raise Exception("Max retries reached")


def fetch_exchange_info():
    url = BINANCE_FUTURES_BASE + "/fapi/v1/exchangeInfo"
    r = rate_limited_request(url)
    return r.json()


def fetch_24hr_ticker():
    url = BINANCE_FUTURES_BASE + "/fapi/v1/ticker/24hr"
    r = rate_limited_request(url)
    return r.json()


def fetch_klines(symbol: str, interval: str = "15m", limit: int = 500):
    url = BINANCE_FUTURES_BASE + "/fapi/v1/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    r = rate_limited_request(url, params=params)
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
    url = BINANCE_FUTURES_BASE + "/fapi/v1/fundingRate"
    params = {"symbol": symbol, "limit": limit}
    r = rate_limited_request(url, params=params)
    arr = r.json()
    return float(arr[-1]["fundingRate"]) if arr else 0.0


def fetch_open_interest(symbol: str):
    url = BINANCE_FUTURES_BASE + "/fapi/v1/openInterest"
    params = {"symbol": symbol}
    r = rate_limited_request(url, params=params)
    return float(r.json().get("openInterest", 0.0))


def fetch_agg_trades(symbol: str, start_time_ms: int = None, limit: int = 1000):
    # approximate CVD by aggregated trades (isBuyerMaker flips)
    url = BINANCE_FUTURES_BASE.replace("fapi", "api") + "/v3/aggTrades"
    params = {"symbol": symbol, "limit": limit}
    if start_time_ms:
        params["startTime"] = start_time_ms
    r = rate_limited_request(url, params=params)
    return r.json()
