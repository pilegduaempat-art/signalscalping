# utils/signals.py
"""
Signal generation and pair selection
"""
import pandas as pd
from datetime import datetime
from api.binance import fetch_24hr_ticker, fetch_klines, fetch_funding_rate, fetch_open_interest
from utils.indicators import atr, approximate_cvd_from_aggtrades
from config import FALLBACK_SYMBOLS


def generate_recommendation(symbol: str, tf: str = "15m"):
    """
    Generate trading recommendation based on multiple factors
    
    Simple rule-based recommendation:
    - Use recent ATR (volatility)
    - Funding rate sign: negative funding suggests more shorts (potential short squeeze long)
    - OI trend: rising OI while price drops -> more shorts
    - CVD: negative big -> selling pressure
    
    Args:
        symbol: Trading pair symbol
        tf: Timeframe for analysis
    
    Returns:
        Dictionary with signal, reason, entry, tp, sl, rr, and other metrics
    """
    try:
        kl = fetch_klines(symbol, interval=tf, limit=50)
        last = kl.iloc[-1]
        recent_atr = atr(kl, period=14).iloc[-1]
        funding = fetch_funding_rate(symbol)
        oi = fetch_open_interest(symbol)
        cvd = approximate_cvd_from_aggtrades(symbol, minutes=60)  # 1h approx

        price = float(last["close"])
        # Basic thresholds (tuneable)
        atr_pct = recent_atr / price if price else 0.0
        big_sell = (cvd is not None and cvd < 0 and abs(cvd) > 0)  # placeholder condition

        signal = "WAIT"
        reason = []
        entry = None
        tp = None
        sl = None
        rr = None

        # Scalp Long logic:
        if funding < -0.0005 and (cvd is not None and cvd < 0):
            # Funding negative and selling pressure -> short-heavy market -> possible short squeeze
            signal = "SCALP LONG"
            entry = price
            tp = price * (1 + max(0.01, min(0.05, atr_pct * 5)))  # 1-5% target scaled by ATR
            sl = price * (1 - max(0.01, min(0.03, atr_pct * 3)))
            reason.append("Funding negative (shorts dominate) + selling pressure -> potential short squeeze")
        # Scalp Short logic:
        elif funding > 0.0005 and (cvd is not None and cvd > 0):
            signal = "SCALP SHORT"
            entry = price
            tp = price * (1 - max(0.01, min(0.05, atr_pct * 5)))
            sl = price * (1 + max(0.01, min(0.03, atr_pct * 3)))
            reason.append("Funding positive + buying pressure -> possible extension to downside reversal")
        else:
            # If large ATR and price dropped strongly -> consider WAIT or SHORT depending
            if atr_pct > 0.03:
                signal = "WAIT"
                reason.append("High volatility – prefer to wait for clearer setup")
            else:
                signal = "WAIT"
                reason.append("No clear short-squeeze or reversal condition")

        if entry and tp and sl:
            potential = (tp - entry) / entry if "LONG" in signal else (entry - tp) / entry
            loss = abs((sl - entry) / entry)
            rr = round((potential / loss) if loss != 0 else None, 2)

        return {
            "symbol": symbol,
            "price": price,
            "funding": funding,
            "oi": oi,
            "cvd": cvd,
            "atr": recent_atr,
            "atr_pct": atr_pct,
            "signal": signal,
            "reason": " ; ".join(reason),
            "entry": entry,
            "tp": tp,
            "sl": sl,
            "rr": rr,
            "ts": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {"symbol": symbol, "error": str(e)}


def get_top_n_pairs_by_volatility(n=10, tf="15m"):
    """
    Get top N most volatile trading pairs
    
    Uses 24h tickers and selects top movers by priceChangePercent magnitude
    
    Args:
        n: Number of pairs to return
        tf: Timeframe (not used currently, for future enhancements)
    
    Returns:
        List of trading pair symbols
    """
    try:
        tickers = fetch_24hr_ticker()
        # Filter perpetual futures symbols (USDT perpetual)
        fut = [t for t in tickers if t["symbol"].endswith("USDT") and ("PERP" not in t)]  # filtering heuristic
        df = pd.DataFrame(fut)
        df["priceChangePercent"] = df["priceChangePercent"].astype(float)
        df["abs_change"] = df["priceChangePercent"].abs()
        top = df.sort_values("abs_change", ascending=False).head(n)
        return top["symbol"].tolist()
    except Exception:
        # fallback list
        return FALLBACK_SYMBOLS[:n]
