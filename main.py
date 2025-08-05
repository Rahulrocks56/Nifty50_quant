import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import time

st.set_page_config(page_title="Nifty 50 Simulator", layout="wide")

# Initialize session state
if "price_data" not in st.session_state:
    st.session_state.price_data = pd.DataFrame(columns=["timestamp", "open", "high", "low", "close"])

# Simulate new ticks
def generate_tick():
    base = 24500
    spread = np.random.randint(-20, 20)
    tick = {
        "timestamp": pd.Timestamp.now(),
        "open": base + spread,
        "high": base + spread + np.random.randint(0, 10),
        "low": base + spread - np.random.randint(0, 10),
        "close": base + spread + np.random.randint(-5, 5)
    }
    return tick

# Real-time tick stream
placeholder = st.empty()
while True:
    tick = generate_tick()
    new_row = pd.DataFrame([tick])
    st.session_state.price_data = pd.concat([st.session_state.price_data, new_row]).tail(30)

    fig = go.Figure(data=[go.Candlestick(
        x=st.session_state.price_data["timestamp"],
        open=st.session_state.price_data["open"],
        high=st.session_state.price_data["high"],
        low=st.session_state.price_data["low"],
        close=st.session_state.price_data["close"]
    )])
    fig.update_layout(title="Live Nifty 50 Simulated Chart", xaxis_rangeslider_visible=False)

    placeholder.plotly_chart(fig, use_container_width=True)
    time.sleep(5)
