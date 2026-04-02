import yfinance as yf
import pandas as pd
import time
import ta
import threading
import requests

print("🚀 BOT INICIANDO...")

TELEGRAM_TOKEN = "8748500939:AAHAG6DctidBW4fVp2QQWgbiI-7mjWXt0O8"
CHAT_ID = "8784442046"

# =========================
# TELEGRAM
# =========================
def send(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
    except Exception as e:
        print("Erro Telegram:", e)

# =========================
# DADOS (YFINANCE)
# =========================
def get_data(symbol):
    try:
        ticker = "BTC-USD" if "BTC" in symbol else "ETH-USD"

        df = yf.download(ticker, period="1d", interval="5m")

        if df.empty:
            print("Sem dados:", symbol)
            return None

        df = df.rename(columns={
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume"
        })

        return df

    except Exception as e:
        print("Erro yfinance:", e)
        return None

# =========================
# CONTROLE
# =========================
last_signal = {}

def analyze(symbol):
    df = get_data(symbol)

    if df is None or df.empty:
        return

    df["rsi"] = ta.momentum.RSIIndicator(df["close"]).rsi()
    df["ema9"] = ta.trend.EMAIndicator(df["close"], 9).ema_indicator()
    df["ema21"] = ta.trend.EMAIndicator(df["close"], 21).ema_indicator()

    last = df.iloc[-1]

    print(f"{symbol} RSI:", round(last["rsi"], 2))

    signal = None

    if last["rsi"] < 35:
        signal = "COMPRA"
    elif last["rsi"] > 65:
        signal = "VENDA"

    if not signal:
        return

    if last_signal.get(symbol) == signal:
        return

    last_signal[symbol] = signal

    entry = last["close"]
    target = entry * 1.02 if signal == "COMPRA" else entry * 0.98
    stop = entry * 0.98 if signal == "COMPRA" else entry * 1.02

    msg = f"""
🚨 SINAL IA

Ativo: {symbol}
Preço: {round(entry,2)}

RSI: {round(last['rsi'],2)}

🎯 Alvo: {round(target,2)}
🛑 Stop: {round(stop,2)}

AÇÃO: {signal}
"""

    send(msg)
    print(msg)

# =========================
# LOOP PRINCIPAL
# =========================
def run_bot():
    while True:
        try:
            print("🔄 Nova execução...")

            analyze("BTCUSDT")
            analyze("ETHUSDT")

            print("✅ Bot rodando...\n")
            time.sleep(300)

        except Exception as e:
            print("Erro:", e)
            time.sleep(30)

# =========================
# KEEP ALIVE
# =========================
def keep_alive():
    while True:
        print("💓 Servidor ativo...")
        time.sleep(60)

# =========================
# THREADS
# =========================
threading.Thread(target=run_bot).start()
threading.Thread(target=keep_alive).start()

while True:
    time.sleep(1)
