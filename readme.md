# 📈 Nifty 50 Real-Time Streamlit Dashboard

This app tracks live Nifty 50 prices from Upstox via WebSocket, overlays key technical indicators, generates trend/breakout alerts, and predicts price movement using XGBoost.

## Features

- ✅ EMA (20 & 50), RSI (14), MACD, ADX, Aroon, Bollinger Bands
- 🚨 Alerts for EMA crossover + Bollinger band breach
- 🕯️ Real-time candlestick chart with auto-refresh
- 🔮 Price prediction (next tick) via XGBoost
- 📲 Telegram & Slack alert integration

## Setup

1. Clone the repo  
   `git clone https://github.com/<your-username>/nifty50-streamlit-dashboard.git`

2. Install dependencies  
   `pip install -r requirements.txt`

3. Configure API keys in `.streamlit/secrets.toml`  
   ```toml
   ACCESS_TOKEN = "your_upstox_access_token"
   TELEGRAM_TOKEN = "your_telegram_bot_token"
   TELEGRAM_CHAT_ID = "your_chat_id"
   SLACK_WEBHOOK_URL = "your_slack_webhook"