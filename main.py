import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from ta.trend import ADXIndicator, AroonIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands
import websockets
import asyncio
import json
import queue
import threading
from datetime import datetime
import pytz

# Configure WebSocket connection
TV_WS_URL = "wss://data.tradingview.com/socket.io/websocket"
SYMBOL = "NSE:NIFTY50"

# Configure Streamlit
st.set_page_config(
    page_title="Nifty 50 Real-Time Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'live_data' not in st.session_state:
    st.session_state.live_data = {
        'price': 0,
        'change': 0,
        'change_percent': 0,
        'volume': 0,
        'timestamp': datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d %H:%M:%S')
    }

# Data processing queue
data_queue = queue.Queue()

class TradingViewWebSocket:
    def __init__(self):
        self.websocket = None
        self.active = False
        self.session_id = "qs_" + str(int(datetime.now().timestamp()))
        
    async def connect(self):
        self.active = True
        try:
            self.websocket = await websockets.connect(TV_WS_URL)
            
            # Initialize connection
            await self.websocket.send(json.dumps({"ts": int(datetime.now().timestamp() * 1000)}))
            await self.websocket.send(json.dumps({
                "text": json.dumps({
                    "locale": "en",
                    "request": "quote_session_start",
                    "session": self.session_id,
                    "device": "desktop",
                    "version": "1.0.0"
                })
            }))
            
            # Subscribe to symbol
            await self.websocket.send(json.dumps({
                "text": json.dumps({
                    "m": "quote_session_add_symbols",
                    "p": [self.session_id, SYMBOL],
                    "session": self.session_id
                })
            }))
            
            # Listen for messages
            while self.active:
                message = await self.websocket.recv()
                data = json.loads(message)
                
                if isinstance(data, list) and len(data) >= 2 and data[0] == "qsd":
                    symbol_data = data[1]
                    if isinstance(symbol_data, dict) and "v" in symbol_data:
                        live_data = {
                            'price': symbol_data["v"].get("lp", 0),
                            'change': symbol_data["v"].get("ch", 0),
                            'change_percent': symbol_data["v"].get("chp", 0),
                            'volume': symbol_data["v"].get("volume", 0),
                            'timestamp': datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d %H:%M:%S')
                        }
                        data_queue.put(live_data)
                        
        except Exception as e:
            st.error(f"WebSocket error: {e}")
        finally:
            self.active = False
            
    def disconnect(self):
        self.active = False
        if self.websocket:
            asyncio.get_event_loop().run_until_complete(self.websocket.close())

# Initialize WebSocket connection
tv_ws = TradingViewWebSocket()
ws_thread = threading.Thread(target=lambda: asyncio.get_event_loop().run_until_complete(tv_ws.connect()))
ws_thread.daemon = True
ws_thread.start()

# Process queue updates
def process_queue_updates():
    while True:
        if not data_queue.empty():
            st.session_state.live_data = data_queue.get()
            data_queue.task_done()

queue_thread = threading.Thread(target=process_queue_updates)
queue_thread.daemon = True
queue_thread.start()

# Technical indicators calculation
def calculate_indicators(prices_df):
    # Convert to numeric
    prices_df['price'] = pd.to_numeric(prices_df['price'])
    
    # ADX
    adx_indicator = ADXIndicator(
        high=prices_df['price'] * 1.001,
        low=prices_df['price'] * 0.999,
        close=prices_df['price'],
        window=14
    )
    prices_df['ADX'] = adx_indicator.adx()
    
    # Aroon
    aroon_indicator = AroonIndicator(prices_df['price'], window=25)
    prices_df['Aroon_Up'] = aroon_indicator.aroon_up()
    prices_df['Aroon_Down'] = aroon_indicator.aroon_down()
    
    # MACD
    macd = MACD(prices_df['price'], window_slow=26, window_fast=12, window_sign=9)
    prices_df['MACD'] = macd.macd()
    prices_df['MACD_Signal'] = macd.macd_signal()
    prices_df['MACD_Hist'] = macd.macd_diff()
    
    # RSI
    rsi_indicator = RSIIndicator(prices_df['price'], window=14)
    prices_df['RSI'] = rsi_indicator.rsi()
    
    # Bollinger Bands
    bb_indicator = BollingerBands(prices_df['price'], window=20, window_dev=2)
    prices_df['BB_upper'] = bb_indicator.bollinger_hband()
    prices_df['BB_lower'] = bb_indicator.bollinger_lband()
    
    return prices_df

# Initialize price history
if 'price_history' not in st.session_state:
    st.session_state.price_history = pd.DataFrame(columns=['timestamp', 'price'])

# Main app layout
st.title("Nifty 50 Live Market Dashboard")

# Display live data
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Current Price", f"₹{st.session_state.live_data['price']:.2f}")
with col2:
    st.metric("Change", f"{st.session_state.live_data['change']:.2f}")
with col3:
    st.metric("% Change", f"{st.session_state.live_data['change_percent']:.2f}%")

# Update price history
if st.session_state.live_data['price'] > 0:
    new_row = {
        'timestamp': datetime.strptime(st.session_state.live_data['timestamp'], '%Y-%m-%d %H:%M:%S'),
        'price': st.session_state.live_data['price']
    }
    st.session_state.price_history = st.session_state.price_history.append(new_row, ignore_index=True)
    
    # Keep only last 100 data points
    if len(st.session_state.price_history) > 100:
        st.session_state.price_history = st.session_state.price_history.iloc[-100:]

# Calculate and display indicators
if len(st.session_state.price_history) > 20:
    indicators_df = calculate_indicators(st.session_state.price_history.copy())
    
    # Plot price and indicators
    fig = go.Figure()
    
    # Price
    fig.add_trace(go.Scatter(
        x=indicators_df['timestamp'],
        y=indicators_df['price'],
        name='Price',
        line=dict(color='blue')
    ))
    
    # Bollinger Bands
    fig.add_trace(go.Scatter(
        x=indicators_df['timestamp'],
        y=indicators_df['BB_upper'],
        name='Upper Band',
        line=dict(color='red', dash='dash')
    ))
    
    fig.add_trace(go.Scatter(
        x=indicators_df['timestamp'],
        y=indicators_df['BB_lower'],
        name='Lower Band',
        line=dict(color='green', dash='dash'),
        fill='tonexty'
    ))
    
    fig.update_layout(
        title='Price with Bollinger Bands',
        xaxis_title='Time',
        yaxis_title='Price'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Display latest indicator values
    st.subheader("Latest Indicator Values")
    st.write(f"RSI: {indicators_df['RSI'].iloc[-1]:.2f}")
    st.write(f"ADX: {indicators_df['ADX'].iloc[-1]:.2f}")
    st.write(f"Aroon Up: {indicators_df['Aroon_Up'].iloc[-1]:.2f}")
    st.write(f"Aroon Down: {indicators_df['Aroon_Down'].iloc[-1]:.2f}")
    st.write(f"MACD: {indicators_df['MACD'].iloc[-1]:.2f}")

st.caption(f"Last updated: {st.session_state.live_data['timestamp']}")
