import websocket
import json
import threading
import time
import logging

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global storage for live data
live_data = {}

def on_message(ws, message):
    try:
        data = json.loads(message)
        token = data.get("instrument_token")
        if token:
            live_data[token] = data
            logger.info(f"Updated data for {token}")
    except Exception as e:
        logger.error(f"Error in on_message: {e}")

def on_error(ws, error):
    logger.error(f"WebSocket Error: {error}")

def on_close(ws, close_status_code, close_msg):
    logger.warning(f"WebSocket Closed: {close_status_code} - {close_msg}")

def on_open(ws):
    def subscribe():
        tokens = ["nse_eq|11630", "nse_eq|3045"]  # Extend as needed
        subscription = {
            "action": "subscribe",
            "params": {"symbols": tokens}
        }
        ws.send(json.dumps(subscription))
        logger.info("Subscription message sent.")
    threading.Thread(target=subscribe).start()

def start_stream(api_key, access_token):
    """
    Starts the Upstox WebSocket stream.
    """
    ws_url = f"wss://example.upstox.com/feed?apiKey={api_key}&accessToken={access_token}"
    ws = websocket.WebSocketApp(ws_url,
                                on_open=on_open,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    ws.run_forever(ping_interval=30, ping_timeout=10)

def get_live_data():
    """
    Returns the latest live data snapshot.
    """
    return live_data
