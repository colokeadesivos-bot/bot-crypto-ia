import requests
import threading
import time
import numpy as np

# =========================
# CONFIG
# =========================
TELEGRAM_TOKEN = "8748500939:AAHAG6DctidBW4fVp2QQWgbiI-7mjWXt0O8"
CHAT_ID = "8784442046"

SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT"]

ULTIMO_DADO = {}

# =========================
# TELEGRAM
# =========================
def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
    except:
        print("Erro Telegram")

# =========================
# APIS
# =========================
def get_bybit(symbol):
    try:
        url = "https://api.bybit.com/v5/market/kline"
        params = {"category": "linear", "symbol": symbol, "interval": "1", "limit": 100}
        r = requests.get(url, params=params, timeout=5)
        data = r.json()

        if data.get("retCode") == 0:
            candles = data["result"]["list"][::-1]
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

        candles = data["data"][::-1]
        return [float(c[4]) for c in candles]

    except:
        return None


# =========================
# MULTI FETCH
# =========================
def fetch_parallel(symbol):
    results = []

    def worker(func):
        data = func(symbol)
        if data and len(data) > 20:
            results.append(data)

    threads = []
    for func in [get_bybit, get_binance, get_okx]:
        t = threading.Thread(target=worker, args=(func,))
        t.start()
        threads.append(t)

    for t in threads:
        t.join(timeout=6)

    if results:
        return results[0]

    return None


def get_data(symbol):
    global ULTIMO_DADO

    data = fetch_parallel(symbol)

    if data:
        ULTIMO_DADO[symbol] = data
        print(f"{symbol} OK")
        return data

    if symbol in ULTIMO_DADO:
        print(f"{symbol} CACHE")
        return ULTIMO_DADO[symbol]

    print(f"{symbol} FALHA TOTAL")
    return None


# =========================
# INDICADORES (SEGURO)
# =========================
def sma(data, period=14):
    data = np.array(data)
    if len(data) < period:
        return None
    return float(np.mean(data[-period:]))


def rsi(data, period=14):
    data = np.array(data)

    if len(data) < period + 1:
        return None

    delta = np.diff(data)

    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)

    avg_gain = np.mean(gain[-period:])
    avg_loss = np.mean(loss[-period:])

    if avg_loss == 0:
        return 100

    rs = avg_gain / avg_loss
    return float(100 - (100 / (1 + rs)))


# =========================
# ESTRATÉGIA (AGRESSIVA)
# =========================
def analyze(symbol):
    data = get_data(symbol)

    if not data:
        return

    price = float(data[-1])

    sma_9 = sma(data, 9)
    sma_21 = sma(data, 21)
    rsi_val = rsi(data, 14)

    if sma_9 is None or sma_21 is None or rsi_val is None:
        return

    # =========================
    # LÓGICA INSANA (AGRESSIVA)
    # =========================
    if sma_9 > sma_21 and rsi_val < 70:
        msg = f"🚀 COMPRA {symbol}\nPreço: {price:.2f}\nRSI: {rsi_val:.1f}"
        print(msg)
        send_telegram(msg)

    elif sma_9 < sma_21 and rsi_val > 30:
        msg = f"🔻 VENDA {symbol}\nPreço: {price:.2f}\nRSI: {rsi_val:.1f}"
        print(msg)
        send_telegram(msg)

    else:
        print(f"{symbol} neutro")


# =========================
# LOOP PRINCIPAL
# =========================
def run_bot():
    print("💎 MODO INSTITUCIONAL ATIVO")

    while True:
        for symbol in SYMBOLS:
            try:
                analyze(symbol)
            except Exception as e:
                print(f"Erro {symbol}: {e}")

        print("⏳ aguardando...\n")
        time.sleep(60)


# =========================
# START
# =========================
if __name__ == "__main__":
    run_bot()
