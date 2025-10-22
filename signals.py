from datetime import datetime
from binance_api import fetch_klines, fetch_funding_rate, fetch_open_interest
from indicators import atr, approximate_cvd_from_aggtrades

def generate_recommendation(symbol: str, tf: str = "15m"):
    try:
        kl = fetch_klines(symbol, interval=tf, limit=50)
        last = kl.iloc[-1]
        recent_atr = atr(kl, period=14).iloc[-1]
        funding = fetch_funding_rate(symbol)
        oi = fetch_open_interest(symbol)
        cvd = approximate_cvd_from_aggtrades(symbol, minutes=60)

        price = float(last["close"])
        atr_pct = recent_atr / price if price else 0.0

        signal = "WAIT"
        reason = []
        entry = tp = sl = rr = None

        if funding < -0.0005 and (cvd is not None and cvd < 0):
            signal = "SCALP LONG"
            entry = price
            tp = price * (1 + max(0.01, min(0.05, atr_pct * 5)))
            sl = price * (1 - max(0.01, min(0.03, atr_pct * 3)))
            reason.append("Funding negative + selling pressure -> short squeeze")

        elif funding > 0.0005 and (cvd is not None and cvd > 0):
            signal = "SCALP SHORT"
            entry = price
            tp = price * (1 - max(0.01, min(0.05, atr_pct * 5)))
            sl = price * (1 + max(0.01, min(0.03, atr_pct * 3)))
            reason.append("Funding positive + buying pressure -> possible reversal")

        else:
            signal = "WAIT"
            reason.append("No clear setup or high volatility")

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
