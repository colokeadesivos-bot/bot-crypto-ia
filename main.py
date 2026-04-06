import requests
import time
import numpy as np

# ==============================
# CONFIG
# ==============================
TOKEN = "SEU_TOKEN_AQUI"
CHAT_ID = "8784442046"

PARES = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT"]

ULTIMO_SINAL = {}

# ==============================
# TELEGRAM
# ==============================
def enviar(msg):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, json={
            "chat_id": CHAT_ID,
            "text": msg,
            "parse_mode": "HTML"
        }, timeout=5)
    except:
        print("Erro Telegram")

# ==============================
# RSI
# ==============================
def calcular_rsi(precos, periodo=14):
    if len(precos) < periodo + 1:
        return None

    delta = np.diff(precos)
    ganhos = np.where(delta > 0, delta, 0)
    perdas = np.where(delta < 0, -delta, 0)

    media_ganho = np.mean(ganhos[-periodo:])
    media_perda = np.mean(perdas[-periodo:])

    if media_perda == 0:
        return 100

    rs = media_ganho / media_perda
    return 100 - (100 / (1 + rs))

# ==============================
# APIs
# ==============================
def get_bybit(symbol):
    try:
        url = "https://api.bybit.com/v5/market/kline"
        params = {
            "category": "linear",
            "symbol": symbol,
            "interval": "1",
            "limit": 100
        }
        r = requests.get(url, params=params, timeout=5)
        data = r.json()

        if data.get("retCode") == 0:
            candles = data["result"]["list"]
            candles = candles[::-1]
            return [float(c[4]) for c in candles]
    except:
        return None

def get_binance(symbol):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1m&limit=100"
        r = requests.get(url, timeout=5)
        data = r.json()
        return [float(c[4]) for c in data]
    except:
        return None

def get_okx(symbol):
    try:
        inst = symbol.replace("USDT", "-USDT")
        url = f"https://www.okx.com/api/v5/market/candles?instId={inst}&bar=1m&limit=100"
        r = requests.get(url, timeout=5)
        data = r.json()

        candles = data.get("data", [])
        candles = candles[::-1]

        return [float(c[4]) for c in candles]
    except:
        return None

# ==============================
# COLETAR DADOS (fallback)
# ==============================
def get_data(symbol):
    for fonte in [get_bybit, get_binance, get_okx]:
        dados = fonte(symbol)
        if dados and len(dados) > 20:
            return dados
    return None

# ==============================
# LÓGICA DE SINAL
# ==============================
def analisar(symbol, precos):
    rsi = calcular_rsi(precos)

    if rsi is None:
        return

    preco = precos[-1]

    sinal = None
    msg = ""

    # SNIPER (entrada forte)
    if rsi < 30:
        sinal = "BUY_SNIPER"
        msg = f"🔥 <b>COMPRA SNIPER {symbol}</b>\nPreço: {preco:.2f}\nRSI: {rsi:.1f}"

    elif rsi > 70:
        sinal = "SELL_SNIPER"
        msg = f"🔻 <b>VENDA FORTE {symbol}</b>\nPreço: {preco:.2f}\nRSI: {rsi:.1f}"

    # Institucional (confirmação)
    elif rsi < 40:
        sinal = "BUY"
        msg = f"📈 <b>Possível COMPRA {symbol}</b>\nRSI: {rsi:.1f}"

    elif rsi > 60:
        sinal = "SELL"
        msg = f"📉 <b>Possível VENDA {symbol}</b>\nRSI: {rsi:.1f}"

    # Anti-spam
    if sinal:
        if ULTIMO_SINAL.get(symbol) != sinal:
            enviar(msg)
            ULTIMO_SINAL[symbol] = sinal

# ==============================
# LOOP PRINCIPAL
# ==============================
print("💎 BOT INSTITUCIONAL ATIVO")

while True:
    for par in PARES:
        dados = get_data(par)

        if dados:
            analisar(par, dados)
        else:
            print(f"{par} sem dados")

    time.sleep(30)
