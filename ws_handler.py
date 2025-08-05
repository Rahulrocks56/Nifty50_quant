import websocket
import json
import threading

ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiI3UkFHVjgiLCJqdGkiOiI2ODkyMmJhOGIzYzczZDI0OGFjYzBmMjIiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlhdCI6MTc1NDQwOTg5NiwiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxNzU0NDMxMjAwfQ.xHVVju2nTY1eAtyCXVFHegoW_DPrNH65pGNWBsy0vfI"
API_KEY = "5b4d759d-de81-4291-8717-ef088ae5a6f9"
INSTRUMENT_TOKEN = "nse_index.nifty"
WS_URL = "wss://feedapi.upstox.com"

price_data = {}

def on_open(ws):
    # Step 1: Authenticate
    auth_msg = {
        "headers": {
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "apiKey": API_KEY
        },
        "method": "authenticate"
    }
    ws.send(json.dumps(auth_msg))

def on_message(ws, message):
    data = json.loads(message)

    # Step 2: Parse Quote Update
    if data.get("type") == "feed_update":
        payload = data.get("payload", [{}])[0]
        symbol = payload.get("instrument", "")
        ltp = payload.get("last_price")
        if symbol and ltp is not None:
            price_data[symbol] = ltp
            print(f"{symbol}: {ltp}")

def on_error(ws, error):
    print("WebSocket error:", error)

def on_close(ws, close_status_code, close_msg):
    print("WebSocket closed")

def stream_prices():
    def run():
        ws = websocket.WebSocketApp(
            WS_URL,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )
        ws.run_forever()

    threading.Thread(target=run).start()
