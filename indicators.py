import pandas as pd
import numpy as np

def calculate_indicators(df):
    df = df.copy()
    df["close"] = pd.to_numeric(df["close"], errors="coerce")

    # 🔁 Ensure minimum data length
    if len(df) < 50:
        return {}

    # 🧮 EMA
    df["EMA_20"] = df["close"].ewm(span=20).mean()
    df["EMA_50"] = df["close"].ewm(span=50).mean()

    # 📉 RSI (14)
    delta = df["close"].diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = pd.Series(gain).rolling(14).mean()
    avg_loss = pd.Series(loss).rolling(14).mean()
    rs = avg_gain / avg_loss
    df["RSI_14"] = 100 - (100 / (1 + rs))

    # 📊 MACD + Histogram
    ema12 = df["close"].ewm(span=12).mean()
    ema26 = df["close"].ewm(span=26).mean()
    df["MACD"] = ema12 - ema26
    df["Signal"] = df["MACD"].ewm(span=9).mean()
    df["MACD_Hist"] = df["MACD"] - df["Signal"]

    # 📈 Bollinger Bands
    df["BB_Mid"] = df["close"].rolling(20).mean()
    df["BB_Std"] = df["close"].rolling(20).std()
    df["BB_Upper"] = df["BB_Mid"] + 2 * df["BB_Std"]
    df["BB_Lower"] = df["BB_Mid"] - 2 * df["BB_Std"]

    # 📍 ADX Calculation (simplified)
    df["TR"] = df["close"].diff().abs()
    df["+DM"] = df["close"].diff().clip(lower=0)
    df["-DM"] = -df["close"].diff().clip(upper=0)
    df["+DI"] = 100 * (df["+DM"].rolling(14).mean() / df["TR"].rolling(14).mean())
    df["-DI"] = 100 * (df["-DM"].rolling(14).mean() / df["TR"].rolling(14).mean())
    df["DX"] = (abs(df["+DI"] - df["-DI"]) / (df["+DI"] + df["-DI"])) * 100
    df["ADX"] = df["DX"].rolling(14).mean()

    # 🔀 Aroon Up/Down (using ranks)
    window = 25
    df["Aroon_Up"] = df["close"].rolling(window).apply(lambda x: 100 * (window - x[::-1].idxmax() % window) / window)
    df["Aroon_Down"] = df["close"].rolling(window).apply(lambda x: 100 * (window - x[::-1].idxmin() % window) / window)

    return df.tail(1).to_dict("records")[0]