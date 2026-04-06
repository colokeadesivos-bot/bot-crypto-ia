import requests
import time
import numpy as np

# ==============================
# CONFIG
# ==============================
CHAT_ID = "8784442046"
TOKEN = "8748500939:AAHAG6DctidBW4fVp2QQWgbiI-7mjWXt0O8"

SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT"]

# ==============================
# TELEGRAM
# ==============================
def send(msg):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": msg})
    except:
        print("Erro Telegram")

# ==============================
# RSI
# ==============================
def rsi(prices, period=14):
    prices = np.array(prices, dtype=float)

    if len(prices) < period + 1:
        return None

    delta = np.diff(prices)
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)

    avg_gain = np.mean(gain[-period:])
    avg_loss = np.mean(loss[-period:])

    if avg_loss == 0:
        return 100

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

# ==============================
# APIs (MULTI BACKUP)
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

        if r.status_code != 200:
            return None

        data = r.json()

        if data.get("retCode") != 0:
            return None

        candles = data["result"]["list"]
        candles.reverse()

        return [float(c[4]) for c in candles]

    except:
        return None


def get_binance(symbol):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1m&limit=100"
        r = requests.get(url, timeout=5)

        if r.status_code != 200:
            return None

        data = r.json()

        if not isinstance(data, list):
            return None

        return [float(c[4]) for c in data]

    except:
        return None


def get_okx(symbol):
    try:
        inst = symbol.replace("USDT", "-USDT")

        url = f"https://www.okx.com/api/v5/market/candles?instId={inst}&bar=1m&limit=100"

        r = requests.get(url, timeout=5)

        if r.status_code != 200:
            return None

        data = r.json()

        if "data" not in data:
            return None

        candles = data["data"]
        candles.reverse()

        return [float(c[4]) for c in candles]

    except:
        return None

# ==============================
# COLETOR INTELIGENTE
# ==============================
def get_data(symbol):
    fontes = [get_bybit, get_binance, get_okx]

    for fonte in fontes:
        data = fonte(symbol)
        if data and len(data) > 20:
            return data

    return None

# ==============================
# MODO INSTITUCIONAL + SNIPER
# ==============================
def analisar(symbol):
    prices = get_data(symbol)

    if not prices:
        print(f"{symbol} sem dados")
        return

    r = rsi(prices)
    price = prices[-1]

    if r is None:
        return

    print(f"{symbol} | RSI: {round(r,1)} | Preço: {price}")

    # ======================
    # SNIPER (ENTRADA FORTE)
    # ======================
    if r < 30:
        send(f"🔥 COMPRA SNIPER {symbol}\nPreço: {price}\nRSI: {round(r,1)}")
    
    elif r > 70:
        send(f"🔥 VENDA SNIPER {symbol}\nPreço: {price}\nRSI: {round(r,1)}")

    # ======================
    # INSTITUCIONAL (CONFIRMAÇÃO)
    # ======================
    elif 30 < r < 40:
        send(f"📈 POSSÍVEL COMPRA {symbol}\nRSI: {round(r,1)}")

    elif 60 < r < 70:
        send(f"📉 POSSÍVEL VENDA {symbol}\nRSI: {round(r,1)}")

# ==============================
# LOOP PRINCIPAL
# ==============================
print("💎 BOT INSTITUCIONAL REAL ATIVO")

while True:
    try:
        for s in SYMBOLS:
            analisar(s)
            time.sleep(2)

        print("⏳ Nova execução...\n")
        time.sleep(15)

    except Exception as e:
        print("Erro geral:", e)
        time.sleep(10)
