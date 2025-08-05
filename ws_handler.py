import websocket
import json
import threading
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global data holder
live_data = {}

def on_message(ws, message):
    try:
        payload = json.loads(message)
        # Assuming Upstox format — adapt as needed
        instrument_token = payload.get("instrument_token")
        if instrument_token:
            live_data[instrument_token] = payload
            logger.info(f"Received data for token: {instrument_token}")
    except Exception as e:
        logger.error(f"Error parsing message: {e}")

def on_error(ws, error):
    logger.error(f"WebSocket error: {error}")

def on_close(ws, close_status_code, close_msg):
    logger.warning("WebSocket connection closed")

def on_open(ws):
    def run():
        # Subscribe to Nifty 50 tokens
        token_list = ["nse_eq|11630", "nse_eq|3045"]  # Add full list here
        subscription_msg = {
            "action": "subscribe",
            "params": {"symbols": token_list}
        }
        ws.send(json.dumps(subscription_msg))
        logger.info("Subscribed to tokens")
    threading.Thread(target=run).start()

def get_live_data():
    return live_data

def start_websocket(api_key, access_token):
    url = f"wss://example.upstox.com/feed?apiKey={api_key}&accessToken={access_token}"
    ws = websocket.WebSocketApp(url,
                                on_open=on_open,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    ws.run_forever(ping_interval=30, ping_timeout=10)
