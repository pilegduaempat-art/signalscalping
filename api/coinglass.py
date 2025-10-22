# api/coinglass.py
"""
Coinglass API calls (optional)
"""
import requests


def fetch_coinglass_metric(symbol: str, metric: str, api_key: str = None):
    """
    Fetch metrics from Coinglass API
    
    Args:
        symbol: Trading pair symbol
        metric: Metric type to fetch
        api_key: Coinglass API key
    
    Returns:
        API response or None if key not provided
    
    Note:
        This is a placeholder. Replace with actual Coinglass endpoints.
        Many Coinglass endpoints are paid; this function is optional.
    """
    if not api_key:
        return None
    
    headers = {"coinglassSecret": api_key}
    
    try:
        url = f"https://openapi.coinglass.com/public/v2/futures/{metric}"
        # This is illustrative. Check Coinglass docs to match endpoints and parameters.
        r = requests.get(url, headers=headers, params={"symbol": symbol}, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None
