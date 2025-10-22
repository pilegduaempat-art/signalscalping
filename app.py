# app.py
"""
Streamlit dashboard + Telegram notifier for automated analysis of top volatile Binance Futures pairs.
Features:
- Fetch top N volatile pairs (by 24h price change or ATR)
- Calculate ATR, approximate CVD (from aggTrades), fetch Open Interest & Funding Rate
- Generate recommendation signals (Scalp Long / Scalp Short / Wait)
- Streamlit UI with charts and auto-refresh
- Telegram notifications for new signals
Requirements:
pip install streamlit pandas requests plotly python-dotenv
Optional: install ccxt if you prefer (not required here)
"""

import time
import pandas as pd
import streamlit as st
import plotly.graph_objs as go
from datetime import datetime

from config import (
    COINGLASS_API_KEY,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    DEFAULT_TOP_N,
    DEFAULT_TIMEFRAME,
    REFRESH_SECONDS
)
from api.binance import fetch_klines
from signals.generator import generate_recommendation
from utils.data import get_top_n_pairs_by_volatility
from utils.telegram import send_telegram_message


# -------------------------
# Streamlit UI
# -------------------------
st.set_page_config(page_title="Binance Futures Auto-Analysis", layout="wide")
st.title("📊 Binance Futures Auto-Analysis – Top Volatile Pairs + Telegram Alerts")

col1, col2 = st.columns([3, 1])

with col2:
    st.write("## Settings")
    top_n = st.number_input("Top N pairs", min_value=1, max_value=50, value=DEFAULT_TOP_N)
    timeframe = st.selectbox("Indicator timeframe (for ATR / signals)", ["1m", "5m", "15m", "1h", "4h"], index=2)
    refresh = st.number_input("Auto-refresh (seconds)", min_value=10, max_value=600, value=REFRESH_SECONDS)
    notify = st.checkbox("Enable Telegram notifications", value=bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID))
    st.write("---")
    st.write("Environment:")
    st.write(f"- Coinglass API: {'✓ configured' if COINGLASS_API_KEY else '✗ not set'}")
    st.write(f"- Telegram: {'✓ configured' if (TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID) else '✗ not set'}")
    manual_refresh = st.button("Refresh Now", key="refresh_button")

with col1:
    placeholder = st.empty()

# State to avoid duplicate notifications
if "last_signals" not in st.session_state:
    st.session_state["last_signals"] = {}

if "last_update" not in st.session_state:
    st.session_state["last_update"] = 0


def main_loop():
    current_time = time.time()
    
    # Auto-refresh logic: update if refresh interval has passed or manual refresh was clicked
    if manual_refresh or (current_time - st.session_state["last_update"] >= refresh):
        st.session_state["last_update"] = current_time
        
        try:
            symbols = get_top_n_pairs_by_volatility(n=top_n, tf=timeframe)
            results = []
            for s in symbols:
                # ensure symbol is in Binance futures format (e.g. BTCUSDT)
                res = generate_recommendation(s, tf=timeframe)
                results.append(res)

            df = pd.DataFrame(results)
            # Show table
            with placeholder.container():
                st.markdown(f"### Top {len(df)} volatile pairs analysis (updated {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC)")
                cols = ["symbol", "price", "atr", "atr_pct", "funding", "oi", "cvd", "signal", "rr", "reason", "ts"]
                display_df = df[cols].copy()
                display_df["price"] = display_df["price"].map(lambda x: round(x, 6) if pd.notnull(x) else x)
                display_df["atr"] = display_df["atr"].map(lambda x: round(x, 6) if pd.notnull(x) else x)
                display_df["atr_pct"] = display_df["atr_pct"].map(lambda x: f"{x*100:.2f}%" if pd.notnull(x) else x)
                display_df["funding"] = display_df["funding"].map(lambda x: f"{x:.6f}" if pd.notnull(x) else x)
                display_df["oi"] = display_df["oi"].map(lambda x: f"{x:.2f}" if pd.notnull(x) else x)
                st.dataframe(display_df, height=420)

                # per-symbol expanders
                for r in results:
                    sym = r.get("symbol")
                    with st.expander(f"{sym} – {r.get('signal')} – price {r.get('price')}"):
                        st.write("**Signal:**", r.get("signal"))
                        st.write("**Reason:**", r.get("reason"))
                        st.write("**Price:**", r.get("price"))
                        st.write("**Funding Rate:**", r.get("funding"))
                        st.write("**Open Interest:**", r.get("oi"))
                        st.write("**CVD (approx):**", r.get("cvd"))
                        st.write("**ATR:**", r.get("atr"), "(abs) |", r.get("atr_pct"))
                        if r.get("entry"):
                            st.write(f"Entry: {r.get('entry'):.6f}, TP: {r.get('tp'):.6f}, SL: {r.get('sl'):.6f}, RRR: {r.get('rr')}")

                        # plot last 100 candles
                        try:
                            kl = fetch_klines(sym, interval=timeframe, limit=200)
                            fig = go.Figure(data=[go.Candlestick(
                                x=kl["open_time"], open=kl["open"], high=kl["high"], low=kl["low"], close=kl["close"],
                                name="Price"
                            )])
                            fig.update_layout(height=300, margin=dict(l=0, r=0, t=20, b=0))
                            st.plotly_chart(fig, use_container_width=True)
                        except Exception as e:
                            st.write("Chart error:", e)

            # Notifications: compare last_signals to current and send new
            for r in results:
                s = r.get("symbol")
                sig = r.get("signal")
                key = f"{s}:{sig}"
                last = st.session_state["last_signals"].get(s)
                # send when a new actionable signal (SCALP LONG/SHORT) appears or changes
                if sig in ["SCALP LONG", "SCALP SHORT"]:
                    if last != sig:
                        st.session_state["last_signals"][s] = sig
                        text = f"*Signal:* {sig}\n*Pair:* {s}\n*Price:* {r.get('price')}\n*TP:* {r.get('tp')}\n*SL:* {r.get('sl')}\n*RRR:* {r.get('rr')}\n*Reason:* {r.get('reason')}"
                        st.write(f"🔔 New signal for {s}: {sig}")
                        if notify:
                            ok = send_telegram_message(text)
                            st.write("Telegram notified:" , ok)
                else:
                    # clear previous if resolved
                    if st.session_state["last_signals"].get(s) and sig == "WAIT":
                        st.session_state["last_signals"].pop(s, None)

        except Exception as e:
            st.error("Error fetching data: " + str(e))
    
    # Schedule next rerun for auto-refresh
    time.sleep(1)
    st.rerun()


# Run main loop
main_loop()

st.markdown("---")
st.caption("Notes: This is a starter dashboard. Tune thresholds, add Coinglass endpoints, and backtest rules before live trading. Use testnet and small sizes.")
