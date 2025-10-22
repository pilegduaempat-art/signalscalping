import time
import pandas as pd
import streamlit as st
import plotly.graph_objs as go
from datetime import datetime

from config import DEFAULT_TOP_N, DEFAULT_TIMEFRAME, REFRESH_SECONDS, COINGLASS_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from signals import generate_recommendation
from utils import get_top_n_pairs_by_volatility, send_telegram_message
from binance_api import fetch_klines

st.set_page_config(page_title="Binance Futures Auto-Analysis", layout="wide")
st.title("📊 Binance Futures Auto-Analysis – Top Volatile Pairs + Telegram Alerts")

col1, col2 = st.columns([3, 1])

with col2:
    st.write("## Settings")
    top_n = st.number_input("Top N pairs", min_value=1, max_value=50, value=DEFAULT_TOP_N)
    timeframe = st.selectbox("Indicator timeframe", ["1m","5m","15m","1h","4h"], index=2)
    refresh = st.number_input("Auto-refresh (seconds)", min_value=10, max_value=600, value=REFRESH_SECONDS)
    notify = st.checkbox("Enable Telegram notifications", value=bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID))
    st.write("---")
    st.write("Environment:")
    st.write(f"- Coinglass API: {'✓ configured' if COINGLASS_API_KEY else '✗ not set'}")
    st.write(f"- Telegram: {'✓ configured' if (TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID) else '✗ not set'}")
    manual_refresh = st.button("Refresh Now")

with col1:
    placeholder = st.empty()

if "last_signals" not in st.session_state:
    st.session_state["last_signals"] = {}

if "last_update" not in st.session_state:
    st.session_state["last_update"] = 0

def main_loop():
    current_time = time.time()
    if current_time - st.session_state["last_update"] >= refresh or manual_refresh:
        st.session_state["last_update"] = current_time
        try:
            symbols = get_top_n_pairs_by_volatility(n=top_n, tf=timeframe)
            results = [generate_recommendation(s, tf=timeframe) for s in symbols]

            df = pd.DataFrame(results)
            with placeholder.container():
                st.markdown(f"### Top {len(df)} volatile pairs (updated {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC)")
                cols = ["symbol","price","atr","atr_pct","funding","oi","cvd","signal","rr","reason","ts"]
                display_df = df[cols].copy()
                display_df["atr_pct"] = display_df["atr_pct"].map(lambda x: f"{x*100:.2f}%" if pd.notnull(x) else x)
                st.dataframe(display_df, height=420)

                for r in results:
                    sym = r.get("symbol")
                    with st.expander(f"{sym} – {r.get('signal')} – price {r.get('price')}"):
                        st.write(r)
                        try:
                            kl = fetch_klines(sym, interval=timeframe, limit=200)
                            fig = go.Figure(data=[go.Candlestick(
                                x=kl["open_time"], open=kl["open"], high=kl["high"], low=kl["low"], close=kl["close"]
                            )])
                            fig.update_layout(height=300)
                            st.plotly_chart(fig, use_container_width=True)
                        except Exception as e:
                            st.write("Chart error:", e)

            for r in results:
                s, sig = r.get("symbol"), r.get("signal")
                last = st.session_state["last_signals"].get(s)
                if sig in ["SCALP LONG", "SCALP SHORT"] and last != sig:
                    st.session_state["last_signals"][s] = sig
                    text = f"*Signal:* {sig}\n*Pair:* {s}\n*Price:* {r.get('price')}\n*TP:* {r.get('tp')}\n*SL:* {r.get('sl')}\n*RRR:* {r.get('rr')}\n*Reason:* {r.get('reason')}"
                    if notify:
                        send_telegram_message(text)
        except Exception as e:
            st.error("Error fetching data: " + str(e))

main_loop()
time.sleep(1)
st.rerun()
st.markdown("---")
st.caption("Notes: Tune thresholds and test carefully before live trading.")
