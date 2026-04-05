import requests
import time
import pandas as pd

TOKEN = "8748500939:AAHAG6DctidBW4fVp2QQWgbiI-7mjWXt0O8"
CHAT_ID = "8784442046"

# =========================
# TELEGRAM
# =========================
def enviar_mensagem(msg):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
    except:
        print("Erro ao enviar mensagem")

# =========================
# DADOS BYBIT
# =========================
def pegar_dados(par):
    try:
        url = f"https://api.bybit.com/v5/market/kline?category=linear&symbol={par}&interval=5&limit=100"
        res = requests.get(url).json()

        lista = res.get("result", {}).get("list", [])

        if not lista:
            return None

        df = pd.DataFrame(lista)

        # Bybit retorna invertido (mais recente primeiro)
        df = df[::-1]

        df = df[[4]]  # preço de fechamento
        df.columns = ["Close"]

        df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
        df.dropna(inplace=True)

        return df

    except Exception as e:
        print(f"Erro Bybit: {e}")
        return None

# =========================
# RSI
# =========================
def calcular_rsi(series, periodo=14):
    delta = series.diff()
    ganho = delta.clip(lower=0)
    perda = -delta.clip(upper=0)

    media_ganho = ganho.rolling(periodo).mean()
    media_perda = perda.rolling(periodo).mean()

    rs = media_ganho / media_perda
    rsi = 100 - (100 / (1 + rs))

    return rsi

# =========================
# ANÁLISE PROFISSIONAL
# =========================
def analisar(df):
    try:
        close = df["Close"]

        if len(close) < 30:
            return None

        ultimo = float(close.iloc[-1])
        anterior = float(close.iloc[-2])

        media_curta = close.rolling(5).mean().iloc[-1]
        media_longa = close.rolling(20).mean().iloc[-1]

        rsi = calcular_rsi(close).iloc[-1]

        variacao = (ultimo - anterior) / anterior

        score = 0

        # Tendência
        if media_curta > media_longa:
            score += 30
        else:
            score -= 30

        # Momentum
        if variacao > 0:
            score += 20
        else:
            score -= 20

        # RSI
        if rsi < 30:
            score += 30
        elif rsi > 70:
            score -= 30

        # DECISÃO
        if score >= 50:
            return f"COMPRA 🚀 | Score: {score} | RSI: {round(rsi,2)}"

        elif score <= -50:
            return f"VENDA 🔻 | Score: {score} | RSI: {round(rsi,2)}"

        else:
            return None

    except Exception as e:
        print("Erro análise:", e)
        return None

# =========================
# LOOP
# =========================
def rodar():
    pares = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT"]

    print("💎 SISTEMA BYBIT ATIVO")

    while True:
        print("🔄 Nova execução...")

        for par in pares:
            df = pegar_dados(par)

            if df is None or df.empty:
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

rodar()
