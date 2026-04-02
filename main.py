import requests
import pandas as pd
import time
import ta
import threading

print("🚀 BOT INICIANDO...")

TELEGRAM_TOKEN = "8748500939:AAHAG6DctidBW4fVp2QQWgbiI-7mjWXt0O8"
CHAT_ID = "8784442046"

# =========================
# TELEGRAM
# =========================
def send(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        r = requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
        print("📩 Telegram:", r.status_code)
    except Exception as e:
        print("Erro Telegram:", e)

# =========================
# DADOS (COINGECKO BLINDADO)
# =========================
def get_data(symbol):
    try:
        pair = "bitcoin" if "BTC" in symbol else "ethereum"

        url = f"https://api.coingecko.com/api/v3/coins/{pair}/market_chart?vs_currency=usd&days=1&interval=minute"
        response = requests.get(url)

        if response.status_code != 200:
            print("Erro API CoinGecko:", response.status_code)
            return None

        data = response.json()

        if "prices" not in data:
            print("Resposta inválida CoinGecko:", data)
            return None

        prices = data["prices"]

        if not prices:
            print("Sem dados de preço")
            return None

        df = pd.DataFrame(prices, columns=["time", "price"])

        df["close"] = df["price"]
        df["open"] = df["price"]
        df["high"] = df["price"]
        df["low"] = df["price"]
        df["volume"] = 1

        return df

    except Exception as e:
        print("Erro CoinGecko:", e)
        return None

# =========================
# CONTROLE
# =========================
last_signal = {}

def analyze(symbol):
    df = get_data(symbol)

    if df is None or df.empty:
        print(f"Sem dados para {symbol}")
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

RSI: {round(last["rsi"],2)}

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
            print("⚠️ Erro geral:", e)
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

# =========================
# LOOP INFINITO (ANTI PARADA)
# =========================
while True:
    time.sleep(1)
