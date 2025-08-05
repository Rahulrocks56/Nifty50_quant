import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import time
import threading

# Upstox SDK v2 imports
import upstox_client
from upstox_client import Configuration, WebSocketClient
from upstox_client.models import *
from upstox_client.rest import ApiException

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
def handle_tick(data):
    try:
        tick = data["data"]
        ltp = tick["last_price"]
        timestamp = pd.Timestamp.now()

        new_row = {
            "timestamp": timestamp,
            "open": ltp,
            "high": ltp + 10,
            "low": ltp - 10,
            "close": ltp
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

# --------------------------- WebSocket Setup ---------------------------
def start_websocket():
    config = Configuration()
    config.access_token = ACCESS_TOKEN
    config.api_key = API_KEY

    ws_client = WebSocketClient(configuration=config)

    def on_message(ws, message):
        handle_tick(message)

    def on_error(ws, error):
        print("WebSocket Error:", error)

    def on_close(ws):
        print("WebSocket Closed")

    ws_client.on_message = on_message
    ws_client.on_error = on_error
    ws_client.on_close = on_close

    ws_client.connect()
    ws_client.subscribe([str(NIFTY_TOKEN)], "full")

# --------------------------- Launch WebSocket ---------------------------
if NIFTY_TOKEN:
    threading.Thread(target=start_websocket).start()
else:
    st.error("Nifty 50 token not found. Unable to stream live data.")
