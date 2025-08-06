import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import websockets
import asyncio
import json
import threading
import queue
from datetime import datetime
import pytz
from ta.trend import ADXIndicator, AroonIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands

# Configure Streamlit page
st.set_page_config(
    page_title="Nifty 50 Real-Time Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Style enhancements
st.markdown("""
<style>
    .metric-card {
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    .bullish {
        background-color: rgba(0,255,0,0.1);
        border-left: 4px solid green;
    }
    .bearish {
        background-color: rgba(255,0,0,0.1);
        border-left: 4px solid red;
    }
    .neutral {
        background-color: rgba(128,128,128,0.1);
        border-left: 4px solid gray;
    }
    .blink {
        animation: blink-animation 1s steps(2, start) infinite;
    }
    @keyframes blink-animation {
        to { opacity: 0.5; }
    }
    .stAlert { padding: 0.5rem !important; }
</style>
""", unsafe_allow_html=True)

# TradingView WebSocket configuration
TV_WS_URL = "wss://data.tradingview.com/socket.io/websocket"
SYMBOL = "NSE:NIFTY50"  # Nifty 50 symbol on TradingView

# Queue for passing data between threads
data_queue = queue.Queue()

# WebSocket client for TradingView
class TradingViewWebSocket:
    def __init__(self):
        self.websocket = None
        self.active = False
        self.session_id = "qs_" + str(int(datetime.now().timestamp()))
        self.packet_count = 1
        
    async def connect(self):
        self.active = True
        self.websocket = await websockets.connect(TV_WS_URL, ping_interval=5)
        
        # Send initialization packets
        await self.send_packet({"ts": int(datetime.now().timestamp() * 1000)})
        await self.send_packet({
            "text": json.dumps({
                "locale": "en",
                "request": "quote_session_start",
                "session": self.session_id,
                "device": "desktop",
                "version": "1.0.0"
            })
        })
        
        # Subscribe to Nifty 50 data
        await self.send_packet({
            "text": json.dumps({
                "m": "quote_session_add_symbols",
                "p": [self.session_id, SYMBOL],
                "session": self.session_id
            })
        })
        
        # Start listening for messages
        while self.active:
            try:
                message = await self.websocket.recv()
                packet = json.loads(message)
                
                if isinstance(packet, list) and len(packet) >= 2:
                    if packet[0] == "qsd":
                        symbol = packet[1][1] if isinstance(packet[1], list) else packet[1]
                        if symbol == SYMBOL:
                            data = {
                                "symbol": symbol,
                                "price": packet[1]["v"]["lp"],
                                "volume": packet[1]["v"]["volume"],
                                "change": packet[1]["v"]["ch"],
                                "change_percent": packet[1]["v"]["chp"],
                                "bid": packet[1]["v"]["bid"],
                                "ask": packet[1]["v"]["ask"],
                                "high": packet[1]["v"]["high_price"],
                                "low": packet[1]["v"]["low_price"],
                                "timestamp": datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d %H:%M:%S')
                            }
                            data_queue.put(data)  # Put data in queue for Streamlit
                            
            except Exception as e:
                st.error(f"WebSocket error: {e}")
                break
                
    async def send_packet(self, packet):
        packet["_ping"] = self.packet_count
        self.packet_count += 1
        await self.websocket.send(json.dumps(packet))
        
    def disconnect(self):
        self.active = False
        if self.websocket:
            asyncio.get_event_loop().run_until_complete(self.websocket.close())

# Start WebSocket in background thread
def start_websocket():
    tv = TradingViewWebSocket()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(tv.connect())

# Initialize WebSocket thread
if 'websocket_thread' not in st.session_state:
    st.session_state.websocket_thread = threading.Thread(target=start_websocket, daemon=True)
    st.session_state.websocket_thread.start()

# Initialize data storage
if 'live_data' not in st.session_state:
    st.session_state.live_data = {}
    st.session_state.price_history = pd.DataFrame(columns=['timestamp', 'price'])
    st.session_state.last_update = datetime.now()

# Process incoming data from queue
def process_queue():
    try:
        while True:
            if not data_queue.empty():
                new_data = data_queue.get()
                st.session_state.live_data = new_data
                
                # Update price history
                new_row = {
                    'timestamp': datetime.now(pytz.timezone('Asia/Kolkata')),
                    'price': new_data['price']
                }
                st.session_state.price_history = st.session_state.price_history.append(new_row, ignore_index=True)
                
                # Keep only last 100 data points
                if len(st.session_state.price_history) > 100:
                    st.session_state.price_history = st.session_state.price_history.iloc[-100:]
                
                st.session_state.last_update = datetime.now()
                
                data_queue.task_done()
    except:
        pass

# Run queue processing in a separate thread
queue_thread = threading.Thread(target=process_queue, daemon=True)
queue_thread.start()

# Technical indicators calculation
def calculate_indicators(df):
    # Convert to numeric
    df['price'] = pd.to_numeric(df['price'])
    
    # Calculate indicators
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    # ADX
    adx_indicator = ADXIndicator(
        high=df['price'] * 1.001, 

