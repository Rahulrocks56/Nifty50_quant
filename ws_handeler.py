import asyncio
import websockets
import json
import pandas as pd
from datetime import datetime

# 📌 Upstox-compatible instrument tokens (you can expand this list)
NIFTY_TOKENS = ["NSE_INDEX_NIFTY"]  # Add more tokens like 'NSE_STOCK_RELIANCE' as needed

# 📦 Cache to hold latest ticks for indicator calculations
price_data = []

# 📡 Format subscription message
def build_subscribe_payload(tokens):
    return json.dumps({
        "guid": "rahul-nifty-tracker",
        "method": "sub",
        "data": {"symbols": tokens}
    })

# 📈 Public function to get the latest DataFrame (used by main.py)
def get_live_data():
    if not price_data:
        return None
    return pd.DataFrame(price_data, columns=["timestamp", "close"])

# 🚀 WebSocket Client
async def stream_prices():
    uri = "wss://api.upstox.com/feed/websocket"  # Replace if a different endpoint
    async with websockets.connect(uri) as ws:
        await ws.send(build_subscribe_payload(NIFTY_TOKENS))

        while True:
            try:
                message = await ws.recv()
                data = json.loads(message)

                # 🧠 Handle quote messages
                if data.get("type") == "quote":
                    ltp = data["data"].get("ltp")
                    ts = datetime.now().strftime("%H:%M:%S")

                    if ltp is not None:
                        # Save to price stream
                        price_data.append([ts, ltp])

                        # ⏳ Keep latest 100 ticks only
                        if len(price_data) > 100:
                            price_data.pop(0)

            except Exception as e:
                print(f"WebSocket Error: {e}")
                continue

# 🧵 Threading wrapper for use in main.py
def start_stream():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(stream_prices())