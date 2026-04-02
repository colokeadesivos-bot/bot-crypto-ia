import requests
import pandas as pd
import time
import ta
import json
import os

print("🚀 BOT INICIANDO...")

TELEGRAM_TOKEN = "8748500939:AAHAG6DctidBW4fVp2QQWgbiI-7mjWXt0O8"
CHAT_ID = "8784442046"

HIST_FILE = "historico.json"
WEIGHTS_FILE = "pesos.json"

# carregar histórico
history = []
if os.path.exists(HIST_FILE):
    with open(HIST_FILE, "r") as f:
        history = json.load(f)

# carregar pesos
weights = {}
if os.path.exists(WEIGHTS_FILE):
    with open(WEIGHTS_FILE, "r") as f:
        weights = json.load(f)

# corrigir formato antigo
if "rsi" in weights:
    print("Corrigindo pesos antigos...")
    weights = {}

last_signal = {}

def save():
    with open(HIST_FILE, "w") as f:
        json.dump(history, f)
    with open(WEIGHTS_FILE, "w") as f:
        json.dump(weights, f)

def send(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
    except Exception as e:
        print("Erro Telegram:", e)

def get_data(symbol):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=15m&limit=200"
    
    try:
        response = requests.get(url)
        data = response.json()

        if not isinstance(data, list):
            print(f"Erro API Binance ({symbol}): {data}")
            return None

        df = pd.DataFrame(data)
        df = df.iloc[:, :6]
        df.columns = ["time","open","high","low","close","volume"]

        return df.astype(float)

    except Exception as e:
        print("Erro ao buscar dados:", e)
        return None

def analyze(symbol):
    global history

    df = get_data(symbol)

    if df is None or df.empty:
        return

    df["rsi"] = ta.momentum.RSIIndicator(df["close"]).rsi()
    df["ema9"] = ta.trend.EMAIndicator(df["close"], 9).ema_indicator()
    df["ema21"] = ta.trend.EMAIndicator(df["close"], 21).ema_indicator()

    last = df.iloc[-1]

    print(f"{symbol} RSI:", last["rsi"])

    signal = None
    trend = "ALTA" if last["ema9"] > last["ema21"] else "BAIXA"

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

    trade = {
        "symbol": symbol,
        "entry": entry,
        "target": target,
        "signal": signal,
        "time": time.time(),
        "result": None
    }

    history.append(trade)
    save()

    msg = f"""
🚨 SINAL IA

Ativo: {symbol}
Entrada: {round(entry,2)}
Alvo: {round(target,2)}

AÇÃO: {signal}
"""
    send(msg)
    print(msg)

def check_results():
    for trade in history:
        if trade["result"] is not None:
            continue

        df = get_data(trade["symbol"])
        if df is None:
            continue

        price = df.iloc[-1]["close"]

        if trade["signal"] == "COMPRA" and price >= trade["target"]:
            trade["result"] = "WIN"
        elif trade["signal"] == "VENDA" and price <= trade["target"]:
            trade["result"] = "WIN"
        elif time.time() - trade["time"] > 1800:
            trade["result"] = "LOSS"

    save()

def run_bot():
    while True:
        try:
            analyze("BTCUSDT")
            analyze("ETHUSDT")
            check_results()

            print("✅ Bot rodando...")
            time.sleep(300)

        except Exception as e:
            print("Erro geral:", e)
            time.sleep(60)

# 🚀 inicia o bot
run_bot()
