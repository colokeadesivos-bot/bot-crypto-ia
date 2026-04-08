import requests
import time
import numpy as np
import json
import os

# =========================
# CONFIG
# =========================
CHAT_ID = "8784442046"
TOKEN = "8748500939:AAHAG6DctidBW4fVp2QQWgbiI-7mjWXt0O8"

SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT"]

STOP_LOSS = 0.02
TAKE_PROFIT = 0.04
RISK = 0.02

balance = 1000
positions = {}

RSI_BUY = 30
RSI_SELL = 70

FILE = "historico.json"

# =========================
# TELEGRAM
# =========================
def send(msg):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": msg})
    except:
        print("Erro Telegram")

# =========================
# HISTÓRICO (IA SIMPLES)
# =========================
def load_history():
    if not os.path.exists(FILE):
        return []
    with open(FILE, "r") as f:
        return json.load(f)

def save_trade(result):
    data = load_history()
    data.append(result)
    with open(FILE, "w") as f:
        json.dump(data, f)

def performance():
    data = load_history()
    if len(data) < 5:
        return 0.5
    wins = sum(1 for x in data if x > 0)
    return wins / len(data)

def ajustar_parametros():
    global RSI_BUY, RSI_SELL

    winrate = performance()

    if winrate < 0.4:
        RSI_BUY = 25
        RSI_SELL = 75
    elif winrate > 0.6:
        RSI_BUY = 35
        RSI_SELL = 65
    else:
        RSI_BUY = 30
        RSI_SELL = 70

    print(f"🧠 Winrate: {round(winrate*100,1)}% | RSI: {RSI_BUY}/{RSI_SELL}")

# =========================
# APIs (BACKUP)
# =========================
def get_bybit(symbol):
    try:
        url = "https://api.bybit.com/v5/market/kline"
        params = {"category": "linear", "symbol": symbol, "interval": "1", "limit": 100}
        r = requests.get(url, params=params, timeout=5).json()
        if r.get("retCode") == 0:
            return [float(c[4]) for c in r["result"]["list"][::-1]]
    except:
        return None

def get_binance(symbol):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1m&limit=100"
        return [float(c[4]) for c in requests.get(url, timeout=5).json()]
    except:
        return None

def get_okx(symbol):
    try:
        inst = symbol.replace("USDT", "-USDT")
        url = f"https://www.okx.com/api/v5/market/candles?instId={inst}&bar=1m&limit=100"
        data = requests.get(url, timeout=5).json()
        return [float(c[4]) for c in data.get("data", [])[::-1]]
    except:
        return None

def get_data(symbol):
    for api in [get_bybit, get_binance, get_okx]:
        data = api(symbol)
        if data and len(data) > 50:
            return data
    return None

# =========================
# INDICADORES
# =========================
def ema(prices, period):
    return np.mean(prices[-period:])

def rsi_inteligente(prices, period=14):
    deltas = np.diff(prices)
    gain = np.maximum(deltas, 0)
    loss = np.abs(np.minimum(deltas, 0))

    avg_gain = np.mean(gain[-period:])
    avg_loss = np.mean(loss[-period:])

    if avg_loss == 0:
        return 100

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    vol = np.std(prices[-20:])
    return rsi - 2 if vol > 0.5 else rsi + 2

# =========================
# FILTROS INSTITUCIONAIS
# =========================
def tendencia_forte(prices):
    return ema(prices, 9) > ema(prices, 21)

def mercado_lateral(prices):
    media = np.mean(prices[-20:])
    return abs(prices[-1] - media) / media < 0.002

def filtro_final(prices):
    media = np.mean(prices[-20:])
    return abs(prices[-1] - media) / media > 0.0015

# =========================
# EXECUÇÃO
# =========================
def abrir(symbol, price):
    global balance
    size = balance * RISK

    positions[symbol] = {
        "entry": price,
        "size": size
    }

    send(f"""
🟢 ENTRADA
{symbol}
Preço: {price}
Valor: {round(size,2)}
""")

def fechar(symbol, price):
    global balance

    entry = positions[symbol]["entry"]
    lucro = (price - entry) / entry

    balance *= (1 + lucro)
    save_trade(lucro)
    ajustar_parametros()

    send(f"""
🔴 SAÍDA
{symbol}
Resultado: {round(lucro*100,2)}%
Banca: {round(balance,2)}
""")

    del positions[symbol]

# =========================
# LOOP PRINCIPAL
# =========================
print("🚀 BOT INSTITUCIONAL 24H ATIVO")

while True:
    for symbol in SYMBOLS:

        prices = get_data(symbol)
        if not prices:
            continue

        price = prices[-1]
        r = rsi_inteligente(prices)

        trend = tendencia_forte(prices)
        lateral = mercado_lateral(prices)
        confirm = filtro_final(prices)

        print(symbol, "| RSI:", round(r,1))

        # =====================
        # ENTRADA
        # =====================
        if symbol not in positions:

            if r < 28 and trend and confirm and not lateral:
                abrir(symbol, price)

            elif r < RSI_BUY and trend and confirm and not lateral:
                abrir(symbol, price)

        # =====================
        # SAÍDA
        # =====================
        else:
            entry = positions[symbol]["entry"]

            if price <= entry * (1 - STOP_LOSS):
                fechar(symbol, price)

            elif price >= entry * (1 + TAKE_PROFIT):
                fechar(symbol, price)

    time.sleep(60)
