# api/coinglass.py
"""
Coinglass API calls (optional)
"""
import requests
from config import COINGLASS_API_KEY


def fetch_coinglass_metric(symbol: str, metric: str):
    """
    Placeholder: fetch from Coinglass (if you have key & correct endpoint).
    Many Coinglass endpoints are paid; this function is optional.
    """
    if not COINGLASS_API_KEY:
        return None
    headers = {"coinglassSecret": COINGLASS_API_KEY}
    # Examples: endpoints must be replaced with real Coinglass endpoints if available.
    try:
        url = f"https://openapi.coinglass.com/public/v2/futures/{metric}"
        # This is illustrative. Check Coinglass docs to match endpoints and parameters.
        r = requests.get(url, headers=headers, params={"symbol": symbol})
        r.raise_for_status()
        return r.json()
    except Exception:
        return None
