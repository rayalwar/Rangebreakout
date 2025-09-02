import os
import time
import datetime as dt
import pandas as pd
from smartapi import SmartConnect

# ---- CONFIG (from Render env variables) ----
API_KEY = os.getenv("API_KEY")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_PWD = os.getenv("CLIENT_PWD")
TOTP_PIN = os.getenv("TOTP_PIN")

symbol_token = "26009"  # BANKNIFTY spot
quantity = 15  # 1 lot
sl_points = 25
target_points = 50

# ---- LOGIN ----
obj = SmartConnect(api_key=API_KEY)
data = obj.generateSession(CLIENT_ID, CLIENT_PWD, TOTP_PIN)
print("✅ Connected to Angel SmartAPI")

def get_candle_data():
    now = dt.datetime.now()
    to_time = now.strftime("%Y-%m-%d %H:%M")
    from_time = (now - dt.timedelta(minutes=60)).strftime("%Y-%m-%d %H:%M")
    params = {
        "exchange": "NSE",
        "symboltoken": symbol_token,
        "interval": "ONE_MINUTE",
        "fromdate": from_time,
        "todate": to_time
    }
    candles = obj.getCandleData(params)
    return pd.DataFrame(candles['data'], columns=["time","open","high","low","close","volume"])

print("⏳ Waiting for 9:45 breakout...")

high_915_945, low_915_945, trade_taken = None, None, False

while True:
    now = dt.datetime.now()

    if now.hour == 9 and now.minute == 45 and not high_915_945:
        df = get_candle_data()
        mask = (pd.to_datetime(df["time"]).dt.time >= dt.time(9,15)) & (pd.to_datetime(df["time"]).dt.time <= dt.time(9,45))
        df_window = df[mask]
        high_915_945, low_915_945 = df_window["high"].max(), df_window["low"].min()
        print(f"📊 9:15–9:45 High={high_915_945}, Low={low_915_945}")

    if high_915_945 and not trade_taken and now >= dt.datetime(now.year, now.month, now.day, 9, 46):
        df = get_candle_data()
        last_close = df.iloc[-1]["close"]

        if last_close > high_915_945:
            print("🚀 Breakout UP! (Place order to Sell ATM PUT)")
            trade_taken = True

        elif last_close < low_915_945:
            print("📉 Breakout DOWN! (Place order to Sell ATM CALL)")
            trade_taken = True

    time.sleep(10)
