# app.py
"""
Streamlit dashboard + Telegram notifier for automated analysis of top volatile Binance Futures pairs.
Features:
- Fetch top N volatile pairs (by 24h price change or ATR)
- Calculate ATR, approximate CVD (from aggTrades), fetch Open Interest & Funding Rate
- Generate recommendation signals (Scalp Long / Scalp Short / Wait)
- Streamlit UI with charts and auto-refresh
- Telegram notifications for new signals
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

# Initialize session state
if "last_signals" not in st.session_state:
    st.session_state["last_signals"] = {}

if "last_update" not in st.session_state:
    st.session_state["last_update"] = 0

if "data_loaded" not in st.session_state:
    st.session_state["data_loaded"] = False

# Layout
col1, col2 = st.columns([3, 1])

with col2:
    st.write("## Settings")
    top_n = st.number_input("Top N pairs", min_value=1, max_value=50, value=DEFAULT_TOP_N, key="top_n_input")
    timeframe = st.selectbox("Indicator timeframe (for ATR / signals)", ["1m", "5m", "15m", "1h", "4h"], index=2, key="tf_select")
    refresh = st.number_input("Auto-refresh (seconds)", min_value=10, max_value=600, value=REFRESH_SECONDS, key="refresh_input")
    notify = st.checkbox("Enable Telegram notifications", value=bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID), key="notify_check")
    st.write("---")
    st.write("Environment:")
    st.write(f"- Coinglass API: {'✓ configured' if COINGLASS_API_KEY else '✗ not set'}")
    st.write(f"- Telegram: {'✓ configured' if (TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID) else '✗ not set'}")
    manual_refresh = st.button("Refresh Now", key="refresh_button")

with col1:
    # Main content placeholder
    main_container = st.container()


def fetch_and_display_data():
    """Fetch data and display in dashboard"""
    try:
        with main_container:
            # Show loading state
            with st.spinner('🔄 Fetching data from Binance...'):
                symbols = get_top_n_pairs_by_volatility(n=top_n, tf=timeframe)
                
                if not symbols:
                    st.error("❌ Could not fetch any symbols. Please check your internet connection.")
                    return
                
                st.info(f"📡 Found {len(symbols)} volatile pairs. Analyzing...")
                
                results = []
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for idx, s in enumerate(symbols):
                    # Update progress
                    progress = (idx + 1) / len(symbols)
                    progress_bar.progress(progress)
                    status_text.text(f"Processing {s}... ({idx + 1}/{len(symbols)})")
                    
                    # Fetch recommendation
                    res = generate_recommendation(s, tf=timeframe)
                    results.append(res)
                    
                    # Add delay between symbols to avoid rate limit
                    time.sleep(0.3)
                
                # Clear progress indicators
                progress_bar.empty()
                status_text.empty()

            if not results:
                st.warning("⚠️ No results to display")
                return

            df = pd.DataFrame(results)
            
            # Filter out rows with errors
            if 'error' in df.columns:
                df_valid = df[df['error'].isna()].copy()
                df_errors = df[df['error'].notna()].copy()
            else:
                df_valid = df.copy()
                df_errors = pd.DataFrame()
            
            # Show errors if any
            if len(df_errors) > 0:
                st.warning(f"⚠️ Failed to fetch data for {len(df_errors)} symbols")
                with st.expander("Show errors"):
                    st.dataframe(df_errors[['symbol', 'error']], use_container_width=True)
            
            # Show table only if we have valid data
            if len(df_valid) > 0:
                st.markdown(f"### 📈 Top {len(df_valid)} volatile pairs analysis")
                st.caption(f"Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
                
                cols = ["symbol", "price", "atr", "atr_pct", "funding", "oi", "cvd", "signal", "rr", "reason"]
                display_df = df_valid[cols].copy()
                
                # Format columns
                display_df["price"] = display_df["price"].map(lambda x: f"{x:.6f}" if pd.notnull(x) else "-")
                display_df["atr"] = display_df["atr"].map(lambda x: f"{x:.6f}" if pd.notnull(x) else "-")
                display_df["atr_pct"] = display_df["atr_pct"].map(lambda x: f"{x*100:.2f}%" if pd.notnull(x) else "-")
                display_df["funding"] = display_df["funding"].map(lambda x: f"{x:.6f}" if pd.notnull(x) else "-")
                display_df["oi"] = display_df["oi"].map(lambda x: f"{x:,.0f}" if pd.notnull(x) else "-")
                display_df["cvd"] = display_df["cvd"].map(lambda x: f"{x:,.2f}" if pd.notnull(x) else "-")
                display_df["rr"] = display_df["rr"].map(lambda x: f"{x:.2f}" if pd.notnull(x) else "-")
                
                # Display table with styling
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    height=400
                )
                
                st.write("---")
                
                # Per-symbol detailed view
                st.subheader("📊 Detailed Analysis")
                
                for idx, r in enumerate(results):
                    if 'error' in r and r.get('error'):
                        continue  # Skip error results
                    
                    sym = r.get("symbol")
                    signal = r.get("signal", "WAIT")
                    price = r.get("price", 0)
                    
                    # Color code based on signal
                    if signal == "SCALP LONG":
                        signal_emoji = "🟢"
                    elif signal == "SCALP SHORT":
                        signal_emoji = "🔴"
                    else:
                        signal_emoji = "⚪"
                    
                    with st.expander(f"{signal_emoji} {sym} – {signal} – ${price:.6f}"):
                        col_a, col_b = st.columns(2)
                        
                        with col_a:
                            st.metric("Signal", signal)
                            st.metric("Price", f"${price:.6f}")
                            st.metric("Funding Rate", f"{r.get('funding', 0):.6f}")
                            st.metric("Open Interest", f"{r.get('oi', 0):,.0f}")
                        
                        with col_b:
                            st.metric("CVD (approx)", f"{r.get('cvd', 0):,.2f}")
                            st.metric("ATR", f"{r.get('atr', 0):.6f}")
                            st.metric("ATR %", f"{r.get('atr_pct', 0)*100:.2f}%")
                            if r.get("rr"):
                                st.metric("Risk/Reward", f"{r.get('rr'):.2f}")
                        
                        st.info(f"**Reason:** {r.get('reason', 'N/A')}")
                        
                        if r.get("entry"):
                            st.success(f"📍 **Entry:** ${r.get('entry'):.6f} | 🎯 **TP:** ${r.get('tp'):.6f} | 🛑 **SL:** ${r.get('sl'):.6f}")
                        
                        # Chart
                        try:
                            with st.spinner(f'Loading chart for {sym}...'):
                                kl = fetch_klines(sym, interval=timeframe, limit=100)
                                fig = go.Figure(data=[go.Candlestick(
                                    x=kl["open_time"],
                                    open=kl["open"],
                                    high=kl["high"],
                                    low=kl["low"],
                                    close=kl["close"],
                                    name="Price"
                                )])
                                fig.update_layout(
                                    height=300,
                                    margin=dict(l=0, r=0, t=20, b=0),
                                    xaxis_rangeslider_visible=False
                                )
                                st.plotly_chart(fig, use_container_width=True)
                        except Exception as e:
                            st.warning(f"Could not load chart: {str(e)}")
                
                # Telegram notifications
                handle_notifications(results, notify)
                
                st.session_state["data_loaded"] = True
                
            else:
                st.error("❌ No valid data available. All symbols failed to fetch.")
                st.session_state["data_loaded"] = False
                
    except Exception as e:
        st.error(f"❌ Error fetching data: {str(e)}")
        st.exception(e)  # Show full traceback for debugging


def handle_notifications(results, notify_enabled):
    """Handle Telegram notifications for new signals"""
    if not notify_enabled:
        return
    
    for r in results:
        if 'error' in r and r.get('error'):
            continue
        
        s = r.get("symbol")
        sig = r.get("signal")
        last = st.session_state["last_signals"].get(s)
        
        # Send when a new actionable signal appears or changes
        if sig in ["SCALP LONG", "SCALP SHORT"]:
            if last != sig:
                st.session_state["last_signals"][s] = sig
                text = f"*Signal:* {sig}\n*Pair:* {s}\n*Price:* ${r.get('price'):.6f}\n*TP:* ${r.get('tp'):.6f}\n*SL:* ${r.get('sl'):.6f}\n*RRR:* {r.get('rr')}\n*Reason:* {r.get('reason')}"
                
                with st.sidebar:
                    st.success(f"🔔 New signal for {s}: {sig}")
                
                if send_telegram_message(text):
                    st.sidebar.info("✅ Telegram notification sent")
                else:
                    st.sidebar.warning("⚠️ Failed to send Telegram notification")
        else:
            # Clear previous if resolved
            if st.session_state["last_signals"].get(s) and sig == "WAIT":
                st.session_state["last_signals"].pop(s, None)


# Main execution logic
current_time = time.time()

# Check if we need to refresh
should_refresh = (
    manual_refresh or 
    not st.session_state["data_loaded"] or
    (current_time - st.session_state["last_update"] >= refresh)
)

if should_refresh:
    st.session_state["last_update"] = current_time
    fetch_and_display_data()
    time.sleep(1)
    st.rerun()
elif st.session_state["data_loaded"]:
    # If data already loaded and not time to refresh, just wait
    time.sleep(1)
    st.rerun()
else:
    # Initial load
    st.info("👆 Click 'Refresh Now' to start fetching data")

# Footer
st.markdown("---")
st.caption("⚠️ **Disclaimer:** This is a starter dashboard for educational purposes. Tune thresholds, add proper backtesting, and use testnet before live trading. Not financial advice.")
