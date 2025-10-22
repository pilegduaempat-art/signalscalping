# utils/indicators.py
"""
Technical indicators calculations
"""
import pandas as pd
from api.binance import fetch_klines


def atr(df: pd.DataFrame, period: int = 14):
    """
    Calculate Average True Range (ATR)
    
    Args:
        df: DataFrame with OHLC data
        period: ATR period
    
    Returns:
        Series with ATR values
    """
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close = (df["low"] - df["close"].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr_series = tr.rolling(period, min_periods=1).mean()
    return atr_series


def approximate_cvd_from_aggtrades(symbol: str, minutes: int = 60):
    """
    Approximate cumulative volume delta using aggregated trades over 'minutes'.
    
    We use taker buy metrics from futures klines (taker_buy_base) and compute 
    delta over last N candles.
    
    Args:
        symbol: Trading pair symbol
        minutes: Number of minutes to analyze
    
    Returns:
        Cumulative volume delta or None if error
    
    Note:
        In aggTrades, there's no isBuyerMaker in the /aggTrades endpoint; 
        instead trade data sometimes lacks taker info. We'll instead use a 
        simple approximation: using taker buy metrics from futures klines 
        (taker_buy_base) and compute delta over last N candles.
    """
    try:
        df = fetch_klines(symbol, interval="1m", limit=minutes)
        # Use taker_buy_base as proxy of aggressive buy volume
        # delta = taker_buy_base - (volume - taker_buy_base)
        df["taker_buy_base"] = df["taker_buy_base"].astype(float)
        df["delta"] = df["taker_buy_base"] - (df["volume"] - df["taker_buy_base"])
        cvd = df["delta"].cumsum().iloc[-1]
        return cvd
    except Exception:
        return None
