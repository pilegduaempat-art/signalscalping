import requests
from config import COINGLASS_API_KEY

def fetch_coinglass_metric(symbol: str, metric: str):
    if not COINGLASS_API_KEY:
        return None
    headers = {"coinglassSecret": COINGLASS_API_KEY}
    try:
        url = f"https://openapi.coinglass.com/public/v2/futures/{metric}"
        r = requests.get(url, headers=headers, params={"symbol": symbol})
        r.raise_for_status()
        return r.json()
    except Exception:
        return None
