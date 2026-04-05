import requests
import numpy as np
import pandas as pd
import time

# ==============================
# TELEGRAM
# ==============================
TOKEN = "8748500939:AAHAG6DctidBW4fVp2QQWgbiI-7mjWXt0O8"
CHAT_ID = "8784442046"

def enviar_mensagem(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg}
    try:
        requests.post(url, data=payload)
    except:
        pass

# ==============================
# BYBIT DATA (CORRIGIDO)
# ==============================
def get_data(symbol="BTCUSDT"):
    url = "https://api.bybit.com/v5/market/kline"

    params = {
        "category": "linear",
        "symbol": symbol,
        "interval": "1",
        "limit": 200
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data["retCode"] != 0:
            print(f"{symbol} erro API")
            return None

        candles = data["result"]["list"]
        candles = candles[::-1]

        closes = [float(c[4]) for c in candles]

        return closes

    except Exception as e:
        print(f"Erro conexão: {e}")
        return None

# ==============================
# INDICADORES
# ==============================
def calcular_ema(data, periodo):
    return pd.Series(data).ewm(span=periodo).mean().iloc[-1]

def calcular_rsi(data, periodo=14):
    series = pd.Series(data)
    delta = series.diff()

    gain = (delta.where(delta > 0, 0)).rolling(periodo).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(periodo).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    return rsi.iloc[-1]

# ==============================
# ESTRATÉGIA (AGRESSIVA)
# ==============================
def analisar(par, dados):
    if dados is None or len(dados) < 50:
        return None

    preco = dados[-1]

    ema9 = calcular_ema(dados, 9)
    ema21 = calcular_ema(dados, 21)
    rsi = calcular_rsi(dados)

    # 🎯 Lógica agressiva
    if preco > ema9 > ema21 and rsi < 70:
        return f"🚀 COMPRA {par}\nPreço: {preco:.2f}\nRSI: {rsi:.1f}"

    if preco < ema9 < ema21 and rsi > 30:
        return f"🔻 VENDA {par}\nPreço: {preco:.2f}\nRSI: {rsi:.1f}"

    return None

# ==============================
# LOOP PRINCIPAL
# ==============================
pares = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT"]

print("💎 BOT INSTITUCIONAL ATIVO")
enviar_mensagem("💎 BOT INSTITUCIONAL ATIVO")

while True:
    print("\n🔄 Nova execução...")

    for par in pares:
        dados = get_data(par)

        if dados is None:
            print(f"{par} sem dados")
            continue

        sinal = analisar(par, dados)

        if sinal:
            print(sinal)
            enviar_mensagem(sinal)
        else:
            print(f"{par} sem sinal")

    time.sleep(60)
