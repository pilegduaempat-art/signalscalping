# api/__init__.py
"""
API module for external data sources
"""
from .binance import (
    fetch_exchange_info,
    fetch_24hr_ticker,
    fetch_klines,
    fetch_funding_rate,
    fetch_open_interest,
    fetch_agg_trades
)
from .coinglass import fetch_coinglass_metric

__all__ = [
    'fetch_exchange_info',
    'fetch_24hr_ticker',
    'fetch_klines',
    'fetch_funding_rate',
    'fetch_open_interest',
    'fetch_agg_trades',
    'fetch_coinglass_metric'
]
