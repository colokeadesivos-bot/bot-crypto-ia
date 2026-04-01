import requests
import pandas as pd
import time
import ta
import json
import os

TELEGRAM_TOKEN = "8748500939:AAHAG6DctidBW4fVp2QQWgbiI-7mjWXt0O8"
CHAT_ID = "8784442046"

HIST_FILE = "historico.json"
WEIGHTS_FILE = "pesos.json"

# 🔥 carregar histórico
if os.path.exists(HIST_FILE):
    with open(HIST_FILE, "r") as f:
        history = json.load(f)
else:
    history = []

# 🔥 carregar pesos com correção automática
if os.path.exists(WEIGHTS_FILE):
    with open(WEIGHTS_FILE, "r") as f:
        weights = json.load(f)
else:
    weights = {}

# 🔥 CORREÇÃO AUTOMÁTICA DE FORMATO ANTIGO
if "rsi" in weights:
    print("Corrigindo estrutura antiga de pesos...")
    weights = {}  # limpa estrutura antiga

last_signal = {}

def save():
    with open(HIST_FILE, "w") as f:
        json.dump(history, f)
    with open(WEIGHTS_FILE, "w") as f:
        json.dump(weights, f)

def send(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

def get_data(symbol):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=15m&limit=200"
    data = requests.get(url).json()

    df = pd.DataFrame(data)
    df = df.iloc[:, :6]
    df.columns = ["time","open","high","low","close","volume"]

    return df.astype(float)

def get_weights(symbol):
    if symbol not in weights:
        weights[symbol] = {"rsi": 1.0, "trend": 1.0, "volume": 1.0}
    return weights[symbol]

def calculate_confidence(df, signal, trend, w):
    last = df.iloc[-1]
    prev = df.iloc[-2]

    score = 50

    if signal == "COMPRA" and last["rsi"] < 30:
        score += 10 * w["rsi"]
    if signal == "VENDA" and last["rsi"] > 70:
        score += 10 * w["rsi"]

    if trend == "ALTA" and signal == "COMPRA":
        score += 10 * w["trend"]
    if trend == "BAIXA" and signal == "VENDA":
        score += 10 * w["trend"]

    if last["volume"] > prev["volume"]:
        score += 10 * w["volume"]

    return min(int(score), 95)

def analyze(symbol):
    global history

    df = get_data(symbol)

    df["rsi"] = ta.momentum.RSIIndicator(df["close"]).rsi()
    df["ema9"] = ta.trend.EMAIndicator(df["close"], 9).ema_indicator()
    df["ema21"] = ta.trend.EMAIndicator(df["close"], 21).ema_indicator()

    last = df.iloc[-1]

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

    w = get_weights(symbol)
    confidence = calculate_confidence(df, signal, trend, w)

    trade = {
        "symbol": symbol,
        "entry": entry,
        "target": target,
        "signal": signal,
        "confidence": confidence,
        "time": time.time(),
        "result": None
    }

    history.append(trade)
    save()

    msg = f"""
🤖 IA EVOLUTIVA

Ativo: {symbol}
Entrada: {round(entry,2)}
Alvo: {round(target,2)}

Confiança: {confidence}%
AÇÃO: {signal}
"""
    send(msg)
    print(msg)

def check_results():
    global weights

    for trade in history:
        if trade["result"] is not None:
            continue

        df = get_data(trade["symbol"])
        price = df.iloc[-1]["close"]

        if trade["signal"] == "COMPRA" and price >= trade["target"]:
            trade["result"] = "WIN"

        elif trade["signal"] == "VENDA" and price <= trade["target"]:
            trade["result"] = "WIN"

        elif time.time() - trade["time"] > 1800:
            trade["result"] = "LOSS"

        else:
            continue

        w = get_weights(trade["symbol"])

        if trade["result"] == "WIN":
            w["rsi"] += 0.1
            w["trend"] += 0.1
            w["volume"] += 0.1
        else:
            w["rsi"] -= 0.05
            w["trend"] -= 0.05
            w["volume"] -= 0.05

    save()

while True:
    try:
        analyze("BTCUSDT")
        analyze("ETHUSDT")
        check_results()

        print("Pesos atualizados:", weights)

        time.sleep(600)

    except Exception as e:
        print("Erro:", e)
        time.sleep(60)
