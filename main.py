import streamlit as st
import pandas as pd
import datetime
import logging
import time
import plotly.graph_objects as go

# 🔧 Config and logging
st.set_page_config(layout="wide")
logging.basicConfig(level=logging.INFO)

# 📦 Persistent OHLCV buffer
if "ohlcv" not in st.session_state:
    st.session_state.ohlcv = {
        "timestamp": [],
        "open": [],
        "high": [],
        "low": [],
        "close": [],
        "volume": [],
    }

# 🛰️ Simulated tick receiver — replace with actual Upstox tick
def receive_tick():
    return {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "price": 19785.75,
        "volume": 1200
    }

# 🔁 Get live OHLCV dataframe
def get_live_data():
    tick = receive_tick()
    ts = pd.to_datetime(tick["timestamp"])
    ohlcv = st.session_state.ohlcv

    if len(ohlcv["timestamp"]) == 0 or ts.minute != pd.to_datetime(ohlcv["timestamp"][-1]).minute:
        # Start new candle
        ohlcv["timestamp"].append(ts)
        ohlcv["open"].append(tick["price"])
        ohlcv["high"].append(tick["price"])
        ohlcv["low"].append(tick["price"])
        ohlcv["close"].append(tick["price"])
        ohlcv["volume"].append(tick["volume"])
    else:
        # Update existing candle
        ohlcv["high"][-1] = max(ohlcv["high"][-1], tick["price"])
        ohlcv["low"][-1] = min(ohlcv["low"][-1], tick["price"])
        ohlcv["close"][-1] = tick["price"]
        ohlcv["volume"][-1] += tick["volume"]

    return pd.DataFrame(ohlcv)

# 📊 Candlestick renderer
def render_candlestick_chart(df):
    fig = go.Figure(data=[go.Candlestick(
        x=df["timestamp"],
        open=df["open"],
        high=df["high"],
        low=df["low"],
        close=df["close"]
    )])
    fig.update_layout(title="Nifty 50 Live Candlestick", xaxis_rangeslider_visible=False)
    return fig

# 📈 Simple RSI calculator (demo version)
def calculate_indicators(df):
    rsi = df["close"].rolling(14).apply(
        lambda x: ((x.diff()[x.diff() > 0].sum() / x.diff().abs().sum()) * 100), raw=True)
    return {"RSI_14": rsi.iloc[-1] if not rsi.empty else None}

# 🔔 Basic alert logic
def check_alerts(indicators):
    rsi_val = indicators.get("RSI_14", 0)
    if rsi_val > 60:
        return {"trend": "Bullish"}
    elif rsi_val < 40:
        return {"trend": "Bearish"}
    return {"trend": "Neutral"}

# 🎯 UI layout
status_placeholder = st.empty()
chart_placeholder = st.empty()
metrics_col1, metrics_col2, metrics_col3 = st.columns(3)

# 🚀 Main refresh cycle
df = get_live_data()

if not df.empty:
    indicators = calculate_indicators(df)
    alerts = check_alerts(indicators)
    last_ts = df["timestamp"].iloc[-1]
    last_price = df["close"].iloc[-1]

    status_placeholder.success(f"✅ Feed Live • Last update: {last_ts}")
    chart_placeholder.plotly_chart(render_candlestick_chart(df), use_container_width=True)

    metrics_col1.metric("Price", f"₹{last_price}")
    metrics_col2.metric("Trend", alerts["trend"])
    metrics_col3.metric("RSI", f"{indicators.get('RSI_14', '--'):.2f}")

    # Wait and rerun safely
    time.sleep(2)
    st.experimental_rerun()
