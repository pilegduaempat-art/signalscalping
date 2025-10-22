# config.py
"""
Configuration file for the Binance Futures Auto-Analysis Dashboard
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Binance API
BINANCE_FUTURES_BASE = "https://fapi.binance.com"

# External APIs (optional - can be configured in UI)
COINGLASS_API_KEY = os.getenv("COINGLASS_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.getenv("TG_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TG_CHAT_ID", "")

# App defaults
DEFAULT_TOP_N = 10
DEFAULT_TIMEFRAME = "15m"
REFRESH_SECONDS = 60

# Available timeframes
TIMEFRAMES = ["1m", "5m", "15m", "1h", "4h"]

# Fallback symbols if API fails
FALLBACK_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "XRPUSDT", "BNBUSDT", "SOLUSDT",
    "LINKUSDT", "ADAUSDT", "DOGEUSDT", "LTCUSDT", "MATICUSDT"
]
