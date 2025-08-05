import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import time
import requests
from upstox_api.api import Upstox
from upstox_api.websocket import WebSocket, LiveFeedType

# --------------------------- Token Fetcher ---------------------------
def get_nifty_token():
    url = "https://assets.upstox.com/instruments/instruments.json"
    try:
        response = requests.get(url)
        response.raise_for_status()
        instruments = response.json()
        for instrument in instruments:
            if instrument.get("instrument_key") == "NSE_INDEX|Nifty 50":
                token = int(instrument.get("exchange_token"))
                print(f"✅ Nifty 50 Token Found: {token}")
                return token
        print("❌ Nifty 50 not found.")
    except Exception as e:
        print("Instrument fetch error:", e)
    return None

# --------------------------- App Settings ---------------------------
st.set_page_config(page_title="Nifty 50 Live Tracker", layout="wide")

API_KEY = "your_api_key_here"
ACCESS_TOKEN = "your_access_token_here"

NIFTY_TOKEN = get_nifty_token()

# --------------------------- Session State ---------------------------
if "price_data" not in st.session_state:
    st.session_state.price_data = pd.DataFrame(columns=["timestamp", "open", "high", "low", "close"])

placeholder = st.empty()

# --------------------------- Tick Handler ---------------------------
def on_tick(tick):
    try:
        tick_data = tick['ltp']
        timestamp = pd.Timestamp.now()

        new_row = {
            "timestamp": timestamp,
            "open": tick_data,
            "high": tick_data + 10,
            "low": tick_data - 10,
            "close": tick_data
        }

        df = pd.DataFrame([new_row])
        st.session_state.price_data = pd.concat([st.session_state.price_data, df]).tail(30)

        fig = go.Figure(data=[go.Candlestick(
            x=st.session_state.price_data["timestamp"],
            open=st.session_state.price_data["open"],
            high=st.session_state.price_data["high"],
            low=st.session_state.price_data["low"],
            close=st.session_state.price_data["close"]
        )])
        fig.update_layout(title="📈 Nifty 50 Live Candlestick Chart", xaxis_rangeslider_visible=False)
        placeholder.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        print("Tick parse error:", e)

def on_error(ws, error):
    print("WebSocket Error:", error)

def on_close(ws):
    print("WebSocket Closed")

def on_open(ws):
    ws.subscribe(NIFTY_TOKEN, LiveFeedType.LTP)

# --------------------------- Start WebSocket ---------------------------
if NIFTY_TOKEN:
    upstox = Upstox(API_KEY, ACCESS_TOKEN)
    upstox.set_access_token(ACCESS_TOKEN)

    socket = WebSocket(API_KEY, ACCESS_TOKEN)
    socket.on_tick = on_tick
    socket.on_error = on_error
    socket.on_close = on_close
    socket.on_open = on_open

    socket.start_websocket()
else:
    st.error("Nifty 50 token not found. Unable to stream live data.")
