import streamlit as st
import websocket
import json
from datetime import datetime
import threading

st.set_page_config(page_title="📈 Nifty 50 Tracker", layout="centered")

st.title("📊 Real-Time Nifty 50 Price")
price_placeholder = st.empty()
time_placeholder = st.empty()
warning_placeholder = st.empty()

# Replace with your actual token and headers
UPSTOX_TOKEN = "your_token_here"
NIFTY_50_TOKEN_ID = "your_instrument_token"  # Confirm from instrument master file

def on_message(ws, message):
    try:
        data = json.loads(message)
        payload = data.get("data", [{}])[0]

        instrument_token = payload.get("instrument_token")
        ltp = payload.get("ltp")
        timestamp = payload.get("exchange_timestamp")

        if ltp and timestamp:
            readable_time = datetime.fromtimestamp(timestamp / 1000)
            price_placeholder.metric("Nifty 50 Price", f"₹{ltp:,.2f}")
            time_placeholder.caption(f"Updated: {readable_time.strftime('%Y-%m-%d %H:%M:%S')}")

            # Price sanity check
            if ltp < 20000:
                warning_placeholder.warning("⚠️ Price seems suspicious. Please verify data source.")
            else:
                warning_placeholder.empty()

            print(f"[{readable_time}] Token: {instrument_token} | Price: ₹{ltp}")
        else:
            st.error("Incomplete data received from WebSocket.")

    except Exception as e:
        st.error(f"Error parsing WebSocket message: {e}")

def on_error(ws, error):
    st.error(f"WebSocket error: {error}")

def on_close(ws):
    st.info("WebSocket connection closed.")

def on_open(ws):
    payload = {
        "guid": "stream_nifty",
        "method": "sub",
        "data": {
            "instrument_tokens": [int(NIFTY_50_TOKEN_ID)]
        }
    }
    ws.send(json.dumps(payload))

def run_websocket():
    ws = websocket.WebSocketApp(
        "wss://api.upstox.com/feed/market-data",
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        header={"Authorization": f"Bearer {UPSTOX_TOKEN}"}
    )
    ws.run_forever()

# Run in a separate thread to avoid Streamlit blocking
threading.Thread(target=run_websocket, daemon=True).start()

# Optional: Fallback NSE API block (commented out)
# import requests
# nse_url = "https://www.nseindia.com/api/quote-equity?symbol=NIFTY"
# headers = {"User-Agent": "Mozilla/5.0"}
# r = requests.get(nse_url, headers=headers)
# data = r.json()
# close_price = data["priceInfo"]["previousClose"]
# st.caption(f"NSE Official Close: ₹{close_price}")
