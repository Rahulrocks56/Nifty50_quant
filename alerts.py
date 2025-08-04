def check_alerts(indicators):
    alerts = {}

    # ⬆️⬇️ Trend Crossover Detection (EMA 20 vs EMA 50)
    ema_20 = indicators.get("EMA_20")
    ema_50 = indicators.get("EMA_50")
    if ema_20 and ema_50:
        if ema_20 > ema_50:
            alerts["trend"] = "🔺 Bullish Crossover"
        elif ema_20 < ema_50:
            alerts["trend"] = "🔻 Bearish Crossover"
        else:
            alerts["trend"] = "➡️ Flat"

    # 📉 Bollinger Band Breakout/Breakdown Detection
    price = indicators.get("close")
    bb_upper = indicators.get("BB_Upper")
    bb_lower = indicators.get("BB_Lower")
    if price and bb_upper and bb_lower:
        if price > bb_upper:
            alerts["bollinger_breakout"] = "🚀 Breakout above Bollinger Band!"
        elif price < bb_lower:
            alerts["bollinger_breakout"] = "⚠️ Breakdown below Bollinger Band!"
        else:
            alerts["bollinger_breakout"] = "📊 Price within range"

    return alerts