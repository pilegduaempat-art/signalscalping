# app.py
"""
Streamlit dashboard + Telegram notifier for automated analysis of top volatile Binance Futures pairs.

Features:
- Fetch top N volatile pairs (by 24h price change or ATR)
- Calculate ATR, approximate CVD (from aggTrades), fetch Open Interest & Funding Rate
- Generate recommendation signals (Scalp Long / Scalp Short / Wait)
- Streamlit UI with charts and auto-refresh
- Telegram notifications for new signals
- Custom API settings in dashboard

Requirements:
pip install streamlit pandas requests plotly python-dotenv
"""

import time
import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from datetime import datetime

# Import configurations
from config import (
    DEFAULT_TOP_N,
    DEFAULT_TIMEFRAME,
    REFRESH_SECONDS,
    TIMEFRAMES,
    COINGLASS_API_KEY as DEFAULT_COINGLASS_KEY,
    TELEGRAM_BOT_TOKEN as DEFAULT_TG_TOKEN,
    TELEGRAM_CHAT_ID as DEFAULT_TG_CHAT_ID
)

# Import functions
from api.binance import fetch_klines
from utils import (
    generate_recommendation,
    get_top_n_pairs_by_volatility,
    send_telegram_message
)

# -------------------------
# Streamlit UI Configuration
# -------------------------
st.set_page_config(
    page_title="Binance Futures Auto-Analysis",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📊 Binance Futures Auto-Analysis – Top Volatile Pairs + Telegram Alerts")

# -------------------------
# Sidebar: Settings & API Configuration
# -------------------------
with st.sidebar:
    st.header("⚙️ Settings")
    
    # Analysis Settings
    st.subheader("Analysis Parameters")
    top_n = st.number_input("Top N pairs", min_value=1, max_value=50, value=DEFAULT_TOP_N)
    timeframe = st.selectbox("Indicator timeframe (for ATR / signals)", TIMEFRAMES, index=TIMEFRAMES.index(DEFAULT_TIMEFRAME))
    refresh = st.number_input("Auto-refresh (seconds)", min_value=10, max_value=600, value=REFRESH_SECONDS)
    
    st.markdown("---")
    
    # API Configuration
    st.subheader("🔑 API Configuration")
    
    # Coinglass API
    with st.expander("Coinglass API (Optional)", expanded=False):
        st.info("Coinglass API provides additional market data. Leave empty if not using.")
        coinglass_key = st.text_input(
            "Coinglass API Key",
            value=DEFAULT_COINGLASS_KEY,
            type="password",
            help="Get your API key from https://www.coinglass.com"
        )
        coinglass_status = "✓ configured" if coinglass_key else "✗ not set"
        st.caption(f"Status: {coinglass_status}")
    
    # Telegram Configuration
    with st.expander("Telegram Notifications", expanded=False):
        st.info("Configure Telegram to receive trading signal alerts.")
        tg_bot_token = st.text_input(
            "Telegram Bot Token",
            value=DEFAULT_TG_TOKEN,
            type="password",
            help="Get bot token from @BotFather on Telegram"
        )
        tg_chat_id = st.text_input(
            "Telegram Chat ID",
            value=DEFAULT_TG_CHAT_ID,
            help="Your personal chat ID or group chat ID"
        )
        notify = st.checkbox(
            "Enable Telegram notifications",
            value=bool(tg_bot_token and tg_chat_id)
        )
        
        tg_status = "✓ configured" if (tg_bot_token and tg_chat_id) else "✗ not set"
        st.caption(f"Status: {tg_status}")
        
        if st.button("🧪 Test Telegram Connection"):
            if tg_bot_token and tg_chat_id:
                test_msg = "🔔 Test message from Binance Futures Auto-Analysis Dashboard"
                success = send_telegram_message(test_msg, tg_bot_token, tg_chat_id)
                if success:
                    st.success("✅ Telegram connection successful!")
                else:
                    st.error("❌ Failed to send message. Check your credentials.")
            else:
                st.warning("⚠️ Please enter both Bot Token and Chat ID first.")
    
    st.markdown("---")
    
    # Manual Refresh Button
    manual_refresh = st.button("🔄 Refresh Now", use_container_width=True)
    
    st.markdown("---")
    
    # Environment Status
    st.subheader("📊 System Status")
    st.caption(f"Coinglass API: {coinglass_status}")
    st.caption(f"Telegram: {tg_status}")
    st.caption(f"Auto-refresh: Every {refresh}s")

# -------------------------
# Main Content Area
# -------------------------
col1, col2 = st.columns([3, 1])

with col2:
    st.metric("Top Pairs", top_n)
    st.metric("Timeframe", timeframe)
    st.metric("Refresh", f"{refresh}s")

with col1:
    placeholder = st.empty()

# -------------------------
# Session State Management
# -------------------------
if "last_signals" not in st.session_state:
    st.session_state["last_signals"] = {}

if "last_update" not in st.session_state:
    st.session_state["last_update"] = 0

# -------------------------
# Main Analysis Loop
# -------------------------
def main_loop():
    """Main analysis and display loop"""
    current_time = time.time()
    
    # Check if it's time to refresh
    if current_time - st.session_state["last_update"] >= refresh or manual_refresh:
        st.session_state["last_update"] = current_time
        
        try:
            # Fetch top volatile pairs
            symbols = get_top_n_pairs_by_volatility(n=top_n, tf=timeframe)
            results = []
            
            # Generate recommendations for each symbol
            with st.spinner(f"Analyzing {len(symbols)} pairs..."):
                for s in symbols:
                    res = generate_recommendation(s, tf=timeframe)
                    results.append(res)

            df = pd.DataFrame(results)
            
            # Display results
            with placeholder.container():
                st.markdown(f"### 📈 Top {len(df)} volatile pairs analysis")
                st.caption(f"Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
                
                # Prepare display dataframe
                cols = ["symbol", "price", "atr", "atr_pct", "funding", "oi", "cvd", "signal", "rr", "reason", "ts"]
                display_df = df[cols].copy()
                display_df["price"] = display_df["price"].map(lambda x: round(x, 6) if pd.notnull(x) else x)
                display_df["atr"] = display_df["atr"].map(lambda x: round(x, 6) if pd.notnull(x) else x)
                display_df["atr_pct"] = display_df["atr_pct"].map(lambda x: f"{x*100:.2f}%" if pd.notnull(x) else x)
                display_df["funding"] = display_df["funding"].map(lambda x: f"{x:.6f}" if pd.notnull(x) else x)
                display_df["oi"] = display_df["oi"].map(lambda x: f"{x:.2f}" if pd.notnull(x) else x)
                
                # Color-code signals
                def highlight_signal(row):
                    if row['signal'] == 'SCALP LONG':
                        return ['background-color: #d4edda'] * len(row)
                    elif row['signal'] == 'SCALP SHORT':
                        return ['background-color: #f8d7da'] * len(row)
                    else:
                        return [''] * len(row)
                
                st.dataframe(
                    display_df.style.apply(highlight_signal, axis=1),
                    height=420,
                    use_container_width=True
                )

                # Per-symbol expanders with charts
                st.markdown("---")
                st.subheader("📊 Detailed Analysis")
                
                for r in results:
                    sym = r.get("symbol")
                    sig = r.get("signal")
                    price = r.get("price")
                    
                    # Color indicator for signal type
                    if sig == "SCALP LONG":
                        indicator = "🟢"
                    elif sig == "SCALP SHORT":
                        indicator = "🔴"
                    else:
                        indicator = "⚪"
                    
                    with st.expander(f"{indicator} {sym} – {sig} – ${price}"):
                        col_a, col_b = st.columns(2)
                        
                        with col_a:
                            st.write("**📊 Signal Information**")
                            st.write(f"**Signal:** {r.get('signal')}")
                            st.write(f"**Price:** ${r.get('price')}")
                            st.write(f"**Funding Rate:** {r.get('funding')}")
                            st.write(f"**Open Interest:** {r.get('oi')}")
                            
                        with col_b:
                            st.write("**📈 Technical Details**")
                            st.write(f"**CVD (approx):** {r.get('cvd')}")
                            st.write(f"**ATR:** {r.get('atr')} ({r.get('atr_pct')})")
                            if r.get("entry"):
                                st.write(f"**Entry:** ${r.get('entry'):.6f}")
                                st.write(f"**TP:** ${r.get('tp'):.6f}")
                                st.write(f"**SL:** ${r.get('sl'):.6f}")
                                st.write(f"**Risk/Reward:** {r.get('rr')}")
                        
                        st.write("**💡 Reason:**", r.get("reason"))
                        
                        # Candlestick chart
                        try:
                            kl = fetch_klines(sym, interval=timeframe, limit=200)
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
                                xaxis_title="Time",
                                yaxis_title="Price",
                                showlegend=False
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        except Exception as e:
                            st.warning(f"⚠️ Chart error: {e}")

            # Telegram Notifications
            if notify and tg_bot_token and tg_chat_id:
                for r in results:
                    s = r.get("symbol")
                    sig = r.get("signal")
                    last = st.session_state["last_signals"].get(s)
                    
                    # Send notification for new actionable signals
                    if sig in ["SCALP LONG", "SCALP SHORT"]:
                        if last != sig:
                            st.session_state["last_signals"][s] = sig
                            text = (
                                f"🔔 *New Signal Alert*\n\n"
                                f"*Signal:* {sig}\n"
                                f"*Pair:* {s}\n"
                                f"*Price:* ${r.get('price')}\n"
                                f"*Entry:* ${r.get('entry'):.6f}\n"
                                f"*TP:* ${r.get('tp'):.6f}\n"
                                f"*SL:* ${r.get('sl'):.6f}\n"
                                f"*RRR:* {r.get('rr')}\n"
                                f"*Reason:* {r.get('reason')}"
                            )
                            
                            success = send_telegram_message(text, tg_bot_token, tg_chat_id)
                            
                            if success:
                                st.toast(f"✅ Telegram alert sent for {s}", icon="✅")
                            else:
                                st.toast(f"⚠️ Failed to send Telegram alert for {s}", icon="⚠️")
                    else:
                        # Clear previous signal if resolved
                        if st.session_state["last_signals"].get(s) and sig == "WAIT":
                            st.session_state["last_signals"].pop(s, None)

        except Exception as e:
            st.error(f"❌ Error fetching data: {str(e)}")
            st.exception(e)

# Run main loop
main_loop()

# Auto-refresh
time.sleep(1)
st.rerun()

# Footer
st.markdown("---")
st.caption(
    "⚠️ **Disclaimer:** This is a starter dashboard for educational purposes. "
    "Tune thresholds, add additional indicators, and backtest rules before live trading. "
    "Always use testnet and small position sizes. Not financial advice."
)
