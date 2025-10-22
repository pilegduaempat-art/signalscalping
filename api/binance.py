# api/binance.py
"""
Binance Futures API calls
"""
import requests
import pandas as pd
from config import BINANCE_FUTURES_BASE


def fetch_exchange_info():
    """Fetch exchange information from Binance Futures"""
    r = requests.get(BINANCE_FUTURES_BASE + "/fapi/v1/exchangeInfo", timeout=10)
    r.raise_for_status()
    return r.json()


def fetch_24hr_ticker():
    """Fetch 24-hour ticker data for all symbols"""
    r = requests.get(BINANCE_FUTURES_BASE + "/fapi/v1/ticker/24hr", timeout=10)
    r.raise_for_status()
    return r.json()


def fetch_klines(symbol: str, interval: str = "15m", limit: int = 500):
    """
    Fetch candlestick/kline data for a symbol
    
    Args:
        symbol: Trading pair symbol (e.g., 'BTCUSDT')
        interval: Timeframe (e.g., '1m', '5m', '15m', '1h', '4h')
        limit: Number of candles to fetch
    
    Returns:
        DataFrame with OHLCV data
    """
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
    """
    Fetch funding rate for a symbol
    
    Args:
        symbol: Trading pair symbol
        limit: Number of funding rate records
    
    Returns:
        Latest funding rate as float
    """
    params = {"symbol": symbol, "limit": limit}
    r = requests.get(BINANCE_FUTURES_BASE + "/fapi/v1/fundingRate", params=params, timeout=10)
    r.raise_for_status()
    arr = r.json()
    return float(arr[-1]["fundingRate"]) if arr else 0.0


def fetch_open_interest(symbol: str):
    """
    Fetch open interest for a symbol
    
    Args:
        symbol: Trading pair symbol
    
    Returns:
        Open interest as float
    """
    params = {"symbol": symbol}
    r = requests.get(BINANCE_FUTURES_BASE + "/fapi/v1/openInterest", params=params, timeout=10)
    r.raise_for_status()
    return float(r.json().get("openInterest", 0.0))


def fetch_agg_trades(symbol: str, start_time_ms: int = None, limit: int = 1000):
    """
    Fetch aggregated trades for CVD calculation
    
    Args:
        symbol: Trading pair symbol
        start_time_ms: Start time in milliseconds
        limit: Number of trades to fetch
    
    Returns:
        List of aggregated trades
    """
    params = {"symbol": symbol, "limit": limit}
    if start_time_ms:
        params["startTime"] = start_time_ms
    r = requests.get(BINANCE_FUTURES_BASE.replace("fapi", "api") + "/v3/aggTrades", params=params, timeout=10)
    r.raise_for_status()
    return r.json()
