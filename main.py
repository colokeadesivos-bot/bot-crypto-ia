import requests
import pandas as pd
import time
import ta
import json
import os

print("🚀 BOT INICIANDO...")

TELEGRAM_TOKEN = "SEU_TOKEN_AQUI"
CHAT_ID = "8784442046"

HIST_FILE = "historico.json"

history = []
if os.path.exists(HIST_FILE):
    try:
        with open(HIST_FILE, "r") as f:
            history = json.load(f)
    except:
        history = []

last_signal = {}

def save():
    with open(HIST_FILE, "w") as f:
        json.dump(history, f)

def send(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        r = requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
        print("📩 Telegram status:", r.status_code)
    except Exception as e:
        print("Erro Telegram:", e)

def get_data(symbol):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=15m&limit=200"
    
    try:
        response = requests.get(url)
        data = response.json()

        if not isinstance(data, list):
            print(f"Erro API Binance ({symbol}):", data)
            return None

        df = pd.DataFrame(data)
        df = df.iloc[:, :6]
        df.columns = ["time","open","high","low","close","volume"]

        return df.astype(float)

    except Exception as e:
        print("Erro ao buscar dados:", e)
        return None

def analyze(symbol):
    df = get_data(symbol)

    if df is None or df.empty:
        return

    df["rsi"] = ta.momentum.RSIIndicator(df["close"]).rsi()
    df["ema9"] = ta.trend.EMAIndicator(df["close"], 9).ema_indicator()
    df["ema21"] = ta.trend.EMAIndicator(df["close"], 21).ema_indicator()

    last = df.iloc[-1]

    print(f"{symbol} RSI:", round(last["rsi"],2))

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

RSI: {round(last["rsi"],2)}

🎯 Alvo: {round(target,2)}
🛑 Stop: {round(stop,2)}

AÇÃO: {signal}
"""

    send(msg)
    print(msg)

def run_bot():
    while True:
        try:
            print("🔄 Nova execução...")

            analyze("BTCUSDT")
            analyze("ETHUSDT")

            print("✅ Bot rodando...\n")
            time.sleep(300)

        except Exception as e:
            print("⚠️ Erro geral:", e)
            time.sleep(30)

# 🚀 inicia o bot
run_bot()
