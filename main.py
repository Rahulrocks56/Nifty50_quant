import json
import websocket
import threading

# Replace these with your actual credentials
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiI3UkFHVjgiLCJqdGkiOiI2ODkyMmJhOGIzYzczZDI0OGFjYzBmMjIiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlhdCI6MTc1NDQwOTg5NiwiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxNzU0NDMxMjAwfQ.xHVVju2nTY1eAtyCXVFHegoW_DPrNH65pGNWBsy0vfI"
INSTRUMENT_TOKEN = "26128"  # Example: 'NSE_INDEX|Nifty 50'

# Define WebSocket URL
UPSTOX_FEED_URL = "wss://api.upstox.com/feed/market-data"

def on_open(ws):
    print("WebSocket connection opened.")

    # Sample subscription payload
    subscribe_payload = {
        "token": ACCESS_TOKEN,
        "type": "subscribe",
        "payload": {
            "instruments": [INSTRUMENT_TOKEN]
        }
    }

    ws.send(json.dumps(subscribe_payload))

def on_message(ws, message):
    try:
        data = json.loads(message)
        print("📈 Incoming Market Data:", data)
    except Exception as e:
        print("❌ Error parsing message:", str(e))

def on_error(ws, error):
    print("⚠️ WebSocket error:", error)

def on_close(ws, close_status_code, close_msg):
    print("🔒 WebSocket closed:", close_status_code, close_msg)

def start_websocket():
    ws = websocket.WebSocketApp(
        UPSTOX_FEED_URL,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws.run_forever()

if __name__ == "__main__":
    print("🚀 Starting Nifty 50 tracker...")
    threading.Thread(target=start_websocket).start()
