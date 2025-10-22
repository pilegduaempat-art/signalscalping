# config.py
"""
Configuration and environment variables
"""
import os
from dotenv import load_dotenv

load_dotenv()

# API Endpoints
BINANCE_FUTURES_BASE = "https://fapi.binance.com"

# API Keys (optional)
COINGLASS_API_KEY = os.getenv("COINGLASS_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TG_CHAT_ID")

# App defaults
DEFAULT_TOP_N = 10
DEFAULT_TIMEFRAME = "15m"
REFRESH_SECONDS = 60
