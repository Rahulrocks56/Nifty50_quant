import streamlit as st
import pandas as pd
import time
import plotly.graph_objects as go

from ws_handler import get_live_data, start_stream
from indicators import calculate_indicators
from alerts import check_alerts
from telegram import Bot
import requests
from xgboost import XGBRegressor
import numpy as np
import threading

# 🛠️ Alert Channels
TELEGRAM_TOKEN = "your_bot_token"
TELEGRAM_CHAT_ID = "your_chat_id"
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/..."

# 🧵 Start WebSocket in background
threading.Thread(target=start_stream, daemon=True).start()

# 🌐 Streamlit Page Setup
st.set_page_config(page_title="📈 Nifty 50 Trend Tracker", layout="wide")
st.title("📉 Nifty 50 Live Dashboard")
st.markdown("---")

# Placeholders
status_placeholder = st.empty()
chart_placeholder = st.empty()
metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
alert_placeholder = st.empty()
predict_placeholder = st.empty()

# 📤 Alert Routing Functions
def send_telegram_alert(message: str):
    bot = Bot(token=TELEGRAM_TOKEN)
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)

def send_slack_alert(message: str):
    payload = {"text": message}
    requests.post(SLACK_WEBHOOK_URL, json=payload)

# 🧠 Prediction Model
def train_predictive_model(df, indicators):
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["epoch"] = df["timestamp"].astype(np.int64) // 10**9
    X = df[["epoch", "EMA_20", "EMA_50", "RSI_14", "MACD", "ADX"]]
    y = df["close"]
    model = XGBRegressor()
    model.fit(X[:-1], y[:-1])
    predicted = model.predict(X[-1:])
    return predicted[0]

# 🕯️ Candlestick Renderer
def render_candlestick_chart(df, indicators):
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df["timestamp"],
        open=df["open"],
        high=df["high"],
        low=df["low"],
        close=df["close"],
        name="Price"
    ))
    fig.add_trace(go.Scatter(x=df["timestamp"], y=df["EMA_20"], mode="lines", name="EMA 20", line=dict(color="blue")))
    fig.add_trace(go.Scatter(x=df["timestamp"], y=df["EMA_50"], mode="lines", name="EMA 50", line=dict(color="orange")))
    fig.update_layout(title="📊 Nifty 50 Candlestick + Signals", xaxis_rangeslider_visible=False)
    return fig

# 🔁 Main Loop
while True:
    df = get_live_data()

    if df is not None and not df.empty:
        indicators = calculate_indicators(df)
        alerts = check_alerts(indicators)
        last_ts = df["timestamp"].iloc[-1]
        last_price = df["close"].iloc[-1]

        status_placeholder.success(f"✅ Feed Live • Last update: {last_ts}")
        chart_placeholder.plotly_chart(render_candlestick_chart(df, indicators), use_container_width=True)

        # 💹 Metrics
        metrics_col1.metric("Price", f"₹{last_price}")
        metrics_col2.metric("Trend", alerts.get("trend", "—"))
        metrics_col3.metric("RSI", f"{indicators.get('RSI_14', '--'):.2f}")

        # 🚨 Alert Display + Push
        alert_msg = alerts.get("bollinger_breakout", "—")
        alert_placeholder.warning(alert_msg)
        if alert_msg != "📊 Price within range":
            send_telegram_alert(alert_msg)
            send_slack_alert(alert_msg)

        # 🔮 Prediction
        prediction = train_predictive_model(df, indicators)
        predict_placeholder.metric("📈 Predicted Price (Next Tick)", f"₹{prediction:.2f}")

    else:
        status_placeholder.error("🔄 Waiting for live data...")

    time.sleep(2)