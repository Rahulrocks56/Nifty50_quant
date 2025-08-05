import streamlit as st
import websocket
import json
from datetime import datetime
import threading

# 💬 App Config
st.set_page_config(page_title="📈 Nifty 50 Tracker", layout="centered")
st.title("📊 Nifty 50 Real-Time Price")

price_box = st.empty()
time_box = st.empty()
warning_box = st.empty()

# 🔐 Replace with actual values
UPSTOX_TOKEN = "your_actual_token_here"
NIFTY_50_TOKEN_ID = "your_instrument_token_here"  # Use correct instrument ID from Upstox

# 📡 Message Handler
def on_message(ws, message):
    try:
        data = json.loads(message)
        payload = data.get("data", [{}])[0]

        # Extract values
        instrument_token = payload.get("instrument_token")
        ltp = payload.get("ltp")
        timestamp = payload.get("exchange_timestamp")

        if ltp and timestamp:
            readable_time = datetime.fromtimestamp(timestamp / 1000)

            price_box.metric("💰 Nifty 50 Price", f"₹{ltp:,.2f}")
            time_box.caption(f"Last updated: {readable_time.strftime('%Y-%m-%d %H:%M:%S')}")

            if ltp < 20000:
                warning_box.warning("⚠️ Received suspiciously low price. Please verify the instrument ID.")
            else:
                warning_box.empty()

            print(f"[{readable_time}] Token: {instrument_token} | Price: ₹{ltp}")
        else:
            st.error("⚠️ Incomplete data received.")

    except Exception as e:
        st.error(f"Error parsing WebSocket message: {e}")
        print("Message Error:", e)

# 🚪 Connection Events
def on_open(ws):
    print("✅ WebSocket connected. Subscribing to Nifty 50...")
    payload = {
        "guid": "nifty_stream",
        "method": "sub",
        "data": {
            "instrument_tokens": [int(NIFTY_50_TOKEN_ID)]
        }
    }
    ws.send(json.dumps(payload))

def on_error(ws, error):
    st.error(f"WebSocket error: {error}")
    print("WebSocket Error:", error)

def on_close(ws):
    st.info("WebSocket connection closed.")
    print("Connection closed.")

# 🔄 Start WebSocket in thread
def run_ws():
    ws = websocket.WebSocketApp(
        "wss://api.upstox.com/feed/market-data",
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        header={"Authorization": f"Bearer {UPSTOX_TOKEN}"}
    )
    ws.run_forever()

threading.Thread(target=run_ws, daemon=True).start()
