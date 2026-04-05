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
        print("Erro Telegram")

# =========================
# BYBIT API (BLINDADO)
# =========================
def pegar_dados(par):
    try:
        url = f"https://api.bybit.com/v5/market/kline?category=linear&symbol={par}&interval=5&limit=100"

        r = requests.get(url, timeout=10)

        if r.status_code != 200:
            return None

        data = r.json()
        lista = data.get("result", {}).get("list", [])

        if not lista:
            return None

        df = pd.DataFrame(lista)
        df = df[::-1]

        df = df[[4]]
        df.columns = ["Close"]

        df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
        df.dropna(inplace=True)

        return df

    except:
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
    return 100 - (100 / (1 + rs))

# =========================
# ANÁLISE INSTITUCIONAL
# =========================
def analisar(df):
    try:
        close = df["Close"]

        if len(close) < 30:
            return None

        ultimo = float(close.iloc[-1])
        anterior = float(close.iloc[-2])

        media5 = float(close.rolling(5).mean().iloc[-1])
        media20 = float(close.rolling(20).mean().iloc[-1])

        rsi = float(calcular_rsi(close).iloc[-1])
        variacao = (ultimo - anterior) / anterior

        score = 0

        # Tendência
        if media5 > media20:
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

        # FILTRO INSTITUCIONAL
        if abs(variacao) < 0.001:
            return None  # evita lateralização

        # DECISÃO
        if score >= 60:
            return {
                "tipo": "COMPRA 🚀",
                "score": score,
                "rsi": round(rsi, 2),
                "preco": round(ultimo, 2)
            }

        elif score <= -60:
            return {
                "tipo": "VENDA 🔻",
                "score": score,
                "rsi": round(rsi, 2),
                "preco": round(ultimo, 2)
            }

        return None

    except Exception as e:
        print("Erro análise:", e)
        return None

# =========================
# GERADOR DE MENSAGEM
# =========================
def formatar_msg(par, sinal):
    return f"""
📊 SINAL INSTITUCIONAL

Ativo: {par}
Tipo: {sinal['tipo']}
Preço: {sinal['preco']}
RSI: {sinal['rsi']}
Score: {sinal['score']}

⚠️ Gestão de risco recomendada
"""

# =========================
# LOOP PRINCIPAL
# =========================
def rodar():
    pares = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT"]

    print("💎 MODO INSTITUCIONAL ATIVO")

    while True:
        print("🔄 Nova execução...")

        for par in pares:
            df = pegar_dados(par)

            if df is None or df.empty:
                print(f"{par} sem dados")
                continue

            sinal = analisar(df)

            if sinal:
                msg = formatar_msg(par, sinal)
                print(msg)
                enviar_mensagem(msg)
            else:
                print(f"{par} filtrado (sem qualidade)")

        print("💓 Sistema rodando...")
        time.sleep(90)

rodar()
