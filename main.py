import time
import requests
import pandas as pd
import numpy as np
import yfinance as yf

# =========================
# CONFIG
# =========================
TOKEN = "8748500939:AAHAG6DctidBW4fVp2QQWgbiI-7mjWXt0O8"
CHAT_ID = "8784442046"

symbols = ["BTC-USD", "ETH-USD", "BNB-USD", "SOL-USD", "XRP-USD"]

# =========================
# TELEGRAM
# =========================
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"Erro Telegram: {e}")

# =========================
# DADOS
# =========================
def get_data(symbol):
    try:
        df = yf.download(symbol, period="1d", interval="5m", progress=False)

        if df is None or df.empty:
            return None

        df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
        df = df.dropna()

        return df
    except Exception as e:
        print(f"Erro dados: {e}")
        return None

# =========================
# INDICADORES
# =========================
def indicators(df):
    df['ema9'] = df['Close'].ewm(span=9).mean()
    df['ema21'] = df['Close'].ewm(span=21).mean()

    delta = df['Close'].diff()
    gain = delta.clip(lower=0).rolling(7).mean()
    loss = (-delta.clip(upper=0)).rolling(7).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))

    df['volatility'] = df['Close'].rolling(10).std()
    df['vol_mean'] = df['Volume'].rolling(10).mean()

    return df

# =========================
# ANÁLISE INSANA (CORRIGIDA)
# =========================
def analyze(df):
    try:
        df = indicators(df)
        df = df.dropna()

        if len(df) < 30:
            return None

        last = df.iloc[-1]
        prev = df.iloc[-2]

        # FORÇAR FLOAT (corrige erro Series)
        close = float(last['Close'])
        prev_close = float(prev['Close'])
        ema9 = float(last['ema9'])
        ema21 = float(last['ema21'])
        rsi = float(last['rsi'])
        volume = float(last['Volume'])
        vol_mean = float(last['vol_mean'])
        volatility = float(last['volatility'])
        avg_volatility = float(df['volatility'].mean())

        signal = None
        score = 0

        # TENDÊNCIA
        if ema9 > ema21:
            trend = "UP"
            score += 1
        else:
            trend = "DOWN"
            score += 1

        # MOMENTO
        if trend == "UP" and rsi < 75:
            signal = "COMPRA"
            score += 1
        elif trend == "DOWN" and rsi > 25:
            signal = "VENDA"
            score += 1

        # VOLUME
        if volume > vol_mean:
            score += 1

        # VOLATILIDADE
        if volatility > avg_volatility:
            score += 1

        # FORÇA DO MOVIMENTO
        movement = abs(close - prev_close) / prev_close
        if movement > 0.001:
            score += 1

        if signal is None:
            return None

        # CONFIANÇA
        confidence = 0.40 + (score * 0.1)

        if confidence < 0.45:
            return None

        # STOP / TARGET
        if signal == "COMPRA":
            stop = close * 0.98
            target = close * 1.03
        else:
            stop = close * 1.02
            target = close * 0.97

        return signal, confidence, close, stop, target

    except Exception as e:
        print(f"Erro análise: {e}")
        return None

# =========================
# LOOP PRINCIPAL
# =========================
def run():
    print("🚀 BOT INSANO INICIANDO...")
    send_telegram("🚀 BOT INSANO ONLINE!")

    while True:
        print("🔄 Nova execução...")

        for symbol in symbols:
            df = get_data(symbol)

            if df is None:
                print(f"Sem dados {symbol}")
                continue

            result = analyze(df)

            if result:
                signal, confidence, entry, stop, target = result

                msg = f"""
💎 SINAL INSANO PRO

📊 Ativo: {symbol}
📈 Direção: {signal}

💰 Entrada: {round(entry,2)}
🎯 Alvo: {round(target,2)}
🛑 Stop: {round(stop,2)}

📊 Confiança: {confidence:.2%}
⚡ Estratégia: IA + Volume + Volatilidade
"""

                print(msg)
                send_telegram(msg)

            else:
                print(f"{symbol} ignorado")

        print("💓 Bot vivo...")
        time.sleep(180)

# =========================
# START
# =========================
if __name__ == "__main__":
    run()
