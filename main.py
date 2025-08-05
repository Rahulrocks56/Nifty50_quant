import streamlit as st
import pandas as pd
import datetime
import requests
import plotly.graph_objects as go
import threading
import json
import websocket
from google.protobuf.json_format import MessageToDict
from upstox_client.feeder.proto import MarketDataFeedV3_pb2 as pb
from streamlit_autorefresh import st_autorefresh

# 🔐 Replace with your actual credentials
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiI3UkFHVjgiLCJqdGkiOiI2ODkyMmJhOGIzYzczZDI0OGFjYzBmMjIiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlhdCI6MTc1NDQwOTg5NiwiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxNzU0NDMxMjAwfQ.xHVVju2nTY1eAtyCXVFHegoW_DPrNH65pGNWBsy0vfI"
BOT_TOKEN = "8327184356:AAFGyU3lQdCm7NbdNEDzkRrwmc6NXw6bb54"
CHAT_ID = "8194487348"

# 🔁 Auto-refresh every 2 seconds
st_autorefresh(interval=2000, limit=None, key="refresh")
st.set_page_config(layout="wide")

# 📦 Session setup
for key in ["ohlcv", "latest_tick", "last_trend", "ws_thread"]:
    if key not in st.session_state:
        st.session_state[key] = {} if key == "ohlcv" else None

st.session_state.ohlcv.update({
    "timestamp": [], "open": [], "high": [], "low": [], "close": [], "volume": []
})

# 📡 WebSocket handlers
def on_message(ws, message):
    try:
        feed = pb.FeedResponse()
        feed.ParseFromString(message)
        data = MessageToDict(feed).get("data", {}).get("payload", {})
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.session_state.latest_tick = {
            "timestamp": ts,
            "price": float(data.get("ltp", 0)),
            "volume": int(data.get("volume", 0))
        }
    except Exception as e:
        print("❌ Protobuf decode failed:", e)

def on_open(ws):
    token = fetch_nifty_token()
    if token:
        ws.send(json.dumps({
            "guid": "nifty-stream",
            "method": "subscribe",
            "data": { "instrumentTokens": [token], "mode": "full" }
        }))

def on_error(ws, err): print("⚠️ WebSocket error:", err)
def on_close(ws, code, reason): print("🔒 Closed:", code, reason)

# 🔗 Authorization helpers
def authorize_websocket():
    url = "https://api.upstox.com/v3/feed/market-data-feed/authorize"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    return requests.post(url, headers=headers).json()["data"]["authorization"]["url"]

def fetch_nifty_token():
    url = "https://api.upstox.com/v2/instruments"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    instruments = requests.get(url, headers=headers).json()["data"]
    for i in instruments:
        if i["segment"] == "NSE_INDEX" and i["trading_symbol"] == "NIFTY 50":
            return i["instrument_token"]

def start_websocket():
    ws_url = authorize_websocket()
    ws = websocket.WebSocketApp(ws_url,
        on_open=on_open, on_message=on_message,
        on_error=on_error, on_close=on_close
    )
    ws.run_forever()

if not st.session_state.ws_thread:
    thread = threading.Thread(target=start_websocket)
    thread.start()
    st.session_state.ws_thread = thread

# 💾 Tick reader
def receive_tick():
    return st.session_state.latest_tick or {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "price": 0,
        "volume": 0
    }

# 🔄 OHLCV Builder
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

# 📊 Indicator logic
def calculate_indicators(df):
    ema9 = df["close"].ewm(span=9).mean()
    ema21 = df["close"].ewm(span=21).mean()
    rsi = df["close"].rolling(14).apply(
        lambda x: ((x.diff()[x.diff() > 0].sum() / x.diff().abs().sum()) * 100), raw=True
    )

    df["H-L"] = df["high"] - df["low"]
    df["H-PC"] = abs(df["high"] - df["close"].shift(1))
    df["L-PC"] = abs(df["low"] - df["close"].shift(1))
    df["TR"] = df[["H-L", "H-PC", "L-PC"]].max(axis=1)

    df["+DM"] = (df["high"] - df["high"].shift(1)).clip(lower=0)
    df["-DM"] = (df["low"].shift(1) - df["low"]).clip(lower=0)

    tr_smooth = df["TR"].rolling(14).mean()
    plus_di = 100 * df["+DM"].rolling(14).mean() / tr_smooth
    minus_di = 100 * df["-DM"].rolling(14).mean() / tr_smooth
    dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
    adx = dx.rolling(14).mean()

    return {
        "RSI": rsi.iloc[-1] if not rsi.empty else None,
        "EMA_9": ema9.iloc[-1] if not ema9.empty else None,
        "EMA_21": ema21.iloc[-1] if not ema21.empty else None,
        "ADX": adx.iloc[-1] if not adx.empty else None
    }

# 🧠 Trend detection
def check_trend(indicators):
    if indicators["EMA_9"] > indicators["EMA_21"] and indicators["ADX"] > 25 and indicators["RSI"] > 60:
        return "Strong Bullish"
    elif indicators["EMA_9"] < indicators["EMA_21"] and indicators["ADX"] > 25 and indicators["RSI"] < 40:
        return "Strong Bearish"
    return "Neutral"

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = { "chat_id": CHAT_ID, "text": message }
    return requests.post(url, data=data).status_code == 200

# 📈 Chart rendering
def render_chart(df):
    fig = go.Figure(data=[go.Candlestick(
        x=df["timestamp"], open=df["open"],
        high=df["high"], low=df["low"], close=df["close"]
    )])
    fig.update_layout(title="Nifty 50 Live Candlestick", xaxis_rangeslider_visible=False)
    return fig

# 🚀 Dashboard Execution
df = get_live_data()
status = st.empty()
chart = st.empty()
col1, col2, col3, col4 = st.columns(4)

if not df.empty:
    indicators = calculate_indicators(df)
    trend = check_trend(indicators)
    ts = df["timestamp"].iloc[-1]
    price = df["close"].iloc[-1]

    status.success(f"✅ Live Feed • Last updated: {ts}")
    chart.plotly_chart(render_chart(df), use_container_width=True)
    col1.metric("Price", f"₹{price}")
    col2.metric("Trend", trend)
    col3.metric("RSI", f"{indicators['RSI']:.2f}")
    col4.metric("ADX", f"{indicators['ADX']:.2f}")

    if trend != st.session_state.last_trend and trend != "Neutral":
        alert_msg = f"📊 {trend} Signal • RSI: {indicators['RSI']:.2f} • ADX: {indicators['ADX']:.2f}"
        if send_telegram_alert(alert_msg):
            st.toast(f"Telegram alert sent: {alert_msg}")
        else:
            st.warning("⚠️

