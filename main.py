import requests
import time
import numpy as np

# =========================
# CONFIG
# =========================
CHAT_ID = "8784442046"
TOKEN = "SEU_TOKEN_AQUI"

SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT"]

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
# APIs (MULTI BACKUP)
# =========================
def get_bybit(symbol):
    try:
        url = "https://api.bybit.com/v5/market/kline"
        params = {"category": "linear", "symbol": symbol, "interval": "1", "limit": 100}
        r = requests.get(url, params=params, timeout=5)
        data = r.json()
        if data.get("retCode") == 0:
            candles = data["result"]["list"]
            return [float(c[4]) for c in candles[::-1]]
    except:
        return None

def get_binance(symbol):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1m&limit=100"
        r = requests.get(url, timeout=5)
        return [float(c[4]) for c in r.json()]
    except:
        return None

def get_okx(symbol):
    try:
        inst = symbol.replace("USDT", "-USDT")
        url = f"https://www.okx.com/api/v5/market/candles?instId={inst}&bar=1m&limit=100"
        r = requests.get(url, timeout=5)
        data = r.json()
        candles = data.get("data", [])
        return [float(c[4]) for c in candles[::-1]]
    except:
        return None

def get_data(symbol):
    for source in [get_bybit, get_binance, get_okx]:
        data = source(symbol)
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

    # ajuste dinâmico
    vol = np.std(prices[-20:])
    return rsi - 2 if vol > 0.5 else rsi + 2

# =========================
# FILTROS INSTITUCIONAIS
# =========================
def tendencia_forte(prices):
    ema9 = ema(prices, 9)
    ema21 = ema(prices, 21)

    direcao = ema9 - ema21
    inclinacao = ema(prices[-5:], 3) - ema(prices[-10:-5], 3)

    return direcao > 0 and inclinacao > 0

def mercado_lateral(prices):
    media = np.mean(prices[-20:])
    ult = prices[-1]
    return abs(ult - media) / media < 0.002

def filtro_final(prices):
    ult = prices[-1]
    media = np.mean(prices[-20:])
    dist = abs(ult - media) / media
    return dist > 0.0015

# =========================
# ANTI-SPAM
# =========================
last_signal = {}

def pode_enviar(symbol, tipo):
    key = f"{symbol}_{tipo}"
    now = time.time()

    if key not in last_signal or now - last_signal[key] > 300:
        last_signal[key] = now
        return True
    return False

# =========================
# LOOP PRINCIPAL
# =========================
print("💎 BOT INSTITUCIONAL ABSURDO ATIVO")

while True:
    for symbol in SYMBOLS:

        prices = get_data(symbol)

        if not prices:
            print(symbol, "sem dados")
            continue

        r = rsi_inteligente(prices)
        price = prices[-1]

        trend = tendencia_forte(prices)
        lateral = mercado_lateral(prices)
        confirm = filtro_final(prices)

        print(f"{symbol} | RSI: {round(r,1)}")

        # =====================
        # 🔥 SNIPER
        # =====================
        if r < 28 and trend and confirm and not lateral:
            if pode_enviar(symbol, "SNIPER"):
                send(f"🔥 COMPRA SNIPER {symbol}\nPreço: {price}\nRSI: {round(r,1)}")

        # =====================
        # 📈 COMPRA
        # =====================
        elif r < 35 and trend and confirm and not lateral:
            if pode_enviar(symbol, "BUY"):
                send(f"📈 COMPRA {symbol}\nPreço: {price}\nRSI: {round(r,1)}")

        # =====================
        # 🔻 VENDA
        # =====================
        elif r > 68 and not trend and confirm:
            if pode_enviar(symbol, "SELL"):
                send(f"🔻 VENDA {symbol}\nPreço: {price}\nRSI: {round(r,1)}")

        else:
            print(symbol, "neutro")

    time.sleep(60)
