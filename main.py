import requests
import time
import os
import pandas as pd
import yfinance as yf

TOKEN = "8748500939:AAHAG6DctidBW4fVp2QQWgbiI-7mjWXt0O8"
CHAT_ID = "8784442046"

# =========================
# ENVIO TELEGRAM
# =========================
def enviar_mensagem(msg):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
    except:
        print("Erro ao enviar mensagem")

# =========================
# PEGAR DADOS CORRETAMENTE
# =========================
def pegar_dados(par):
    try:
        df = yf.download(par, period="1d", interval="5m")

        if df.empty:
            return None

        # 🔥 CORREÇÃO PRINCIPAL AQUI
        df["Close"] = pd.to_numeric(df["Close"], errors="coerce")

        df.dropna(inplace=True)

        return df

    except Exception as e:
        print(f"Erro yfinance: {e}")
        return None

# =========================
# INDICADORES
# =========================
def analisar(df):
    try:
        close = df["Close"]

        # 🔥 GARANTE VALOR ESCALAR
        ultimo = float(close.iloc[-1])
        anterior = float(close.iloc[-2])

        # Médias
        media_curta = float(close.tail(5).mean())
        media_longa = float(close.tail(20).mean())

        # Momentum
        variacao = (ultimo - anterior) / anterior

        # =====================
        # MODO INSANO 🔥
        # =====================
        if media_curta > media_longa and variacao > 0.001:
            return "COMPRA 🚀"

        elif media_curta < media_longa and variacao < -0.001:
            return "VENDA 🔻"

        else:
            return None

    except Exception as e:
        print(f"Erro análise: {e}")
        return None

# =========================
# LOOP PRINCIPAL
# =========================
def rodar():
    pares = ["BTC-USD", "ETH-USD", "BNB-USD", "SOL-USD", "XRP-USD"]

    print("🚀 BOT INSANO INICIANDO...")

    while True:
        print("🔄 Nova execução...")

        for par in pares:
            df = pegar_dados(par)

            if df is None:
                print(f"{par} sem dados")
                continue

            sinal = analisar(df)

            if sinal:
                msg = f"{par} → {sinal}"
                print(msg)
                enviar_mensagem(msg)
            else:
                print(f"{par} ignorado")

        print("💓 Bot vivo...")
        time.sleep(60)

# =========================
# START
# =========================
rodar()
