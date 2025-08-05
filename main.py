import requests
import json
import websocket
import threading

# 🔐 Replace with your actual Upstox access token
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiI3UkFHVjgiLCJqdGkiOiI2ODkyMmJhOGIzYzczZDI0OGFjYzBmMjIiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlhdCI6MTc1NDQwOTg5NiwiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxNzU0NDMxMjAwfQ.xHVVju2nTY1eAtyCXVFHegoW_DPrNH65pGNWBsy0vfI"

# 🧩 Step 1: Fetch instrument token for Nifty 50
def get_nifty_token():
    url = "https://api.upstox.com/v2/instruments"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        instruments = response.json()["data"]
        for instrument in instruments:
            if instrument["segment"] == "NSE_INDEX" and instrument["trading_symbol"] == "NIFTY 50":
                return instrument["instrument_token"]
        print("⚠️ Nifty 50 token not found in instruments list.")
        return None
    else:
        print("❌ Failed to fetch instruments:", response.status_code, response.text)
        return None

# 🔐 Step 2: Authorize WebSocket session
def get_websocket_url():
    url = "https://api.upstox.com/v3/feed/market-data-feed/authorize"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

    response = requests.post(url, headers=headers)
    if response.status_code == 200:
        return response.json()["data"]["authorization"]["url"]
    else:
        print("❌ WebSocket authorization failed:", response.status_code, response.text)
        return None

# 🔗 Step 3: WebSocket Handlers
def on_open(ws):
    print("✅ WebSocket connection opened.")
    nifty_token = get_nifty_token()
    if nifty_token:
        payload = {
            "guid": "rahul-nifty-guid",
            "method": "subscribe",
            "data": {
                "instrumentTokens": [nifty_token],
                "mode": "full"
            }
        }
        ws.send(json.dumps(payload))
    else:
        print("⚠️ Subscription skipped due to missing token.")

def on_message(ws, message):
    try:
        data = json.loads(message)
        print("📈 Market Data:", data)
    except Exception as e:
        print("❌ Message parsing error:", e)

def on_error(ws, error):
    print("⚠️ WebSocket error:", error)

def on_close(ws, code, reason):
    print("🔒 Connection closed:", code, reason)

def start_websocket(url):
    ws = websocket.WebSocketApp(
        url,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws.run_forever()

# 🚀 Main Execution
if __name__ == "__main__":
    print("🔐 Authorizing WebSocket...")
    ws_url = get_websocket_url()
    if ws_url:
        print("🔗 Starting live Nifty 50 feed...")
        threading.Thread(target=start_websocket, args=(ws_url,)).start()
    else:
        print("❌ Could not retrieve WebSocket URL.")
