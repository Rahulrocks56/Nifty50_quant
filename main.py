import streamlit as st
import pandas as pd
import datetime
import requests
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# 🔁 Auto-refresh every 2 seconds
st_autorefresh(interval=2000, limit=None, key="chart_refresh")

# ⚙️ Streamlit config
st.set_page_config(layout="wide")

# 📦 Persistent storage
if "ohlcv" not in st.session_state:
    st.session_state.ohlcv = {
        "timestamp": [],
        "open": [],
        "high": [],
        "low": [],
        "close": [],
        "volume": [],
    }

if "last_trend" not in st.session_state:
    st.session_state.last_trend = None

# 📡 Simulated tick receiver — replace with live feed
def receive_tick():
    return {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "price": 19785.75,
        "volume": 1200
    }

# 🔄 Get live OHLCV data
def get_live_data():
    tick = receive_tick()
    ts = pd.to_datetime(tick["timestamp"])
    ohlcv = st.session_state.ohlcv

    if len(ohlcv["timestamp"]) == 0 or ts.minute != pd.to_datetime(ohlcv["timestamp"][-1]).minute:
        ohlcv["timestamp"].append(ts)
        ohlcv["open"].append(tick["price"])
        ohlcv["high"].append(tick["price"])
        ohlcv["low"].append(tick["price"])
        ohlcv["close"].append(tick["price"])
        ohlcv["volume"].append(tick["volume"])
    else:
        ohlcv["high"][-1] = max(ohlcv["high"][-1], tick["price"])
        ohlcv["low"][-1] = min(ohlcv["low"][-1], tick["price"])
        ohlcv["close"][-1] = tick["price"]
        ohlcv["volume"][-1] += tick["volume"]

    return pd.DataFrame(ohlcv)

# 📊 Chart renderer
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

# 📈 RSI calculator
def calculate_indicators(df):
    rsi = df["close"].rolling(14).apply(
        lambda x: ((x.diff()[x.diff() > 0].sum() / x.diff().abs().sum()) * 100), raw=True)
    return {"RSI_14": rsi.iloc[-1] if not rsi.empty else None}

# 🔔 Trend alert logic
def check_alerts(indicators):
    rsi_val = indicators.get("RSI_14", 0)
    if rsi_val > 60:
        return {"trend": "Bullish"}
    elif rsi_val < 40:
        return {"trend": "Bearish"}
    return {"trend": "Neutral"}

# 📲 Telegram alert sender
def send_telegram_alert(message):
    token = "<YOUR_BOT_TOKEN>"
    chat_id = "<YOUR_CHAT_ID>"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {"chat_id": chat_id, "text": message}
    response = requests.post(url, data=data)
    return response.status_code == 200

# 🚀 Main execution
df = get_live_data()
status_placeholder = st.empty()
chart_placeholder = st.empty()
metrics_col1, metrics_col2, metrics_col3 = st.columns(3)

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

    # 🔔 Alert trigger
    current_trend = alerts["trend"]
    last_trend = st.session_state.last_trend

    if current_trend != last_trend and current_trend != "Neutral":
        alert_msg = f"📊 Trend Change Alert: RSI indicates a {current_trend} setup."
        if send_telegram_alert(alert_msg):
            st.toast(f"Telegram alert sent: {alert_msg}")
        else:
            st.warning("⚠️ Failed to send Telegram alert.")

    st.session_state.last_trend = current_trend
