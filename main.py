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
    except:
        print("Erro Telegram")

# =========================
# DADOS
# =========================
def get_data(symbol):
    try:
        df = yf.download(symbol, period="1d", interval="5m")

        if df is None or df.empty:
            return None

        df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
        df.dropna(inplace=True)

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
    gain = (delta.where(delta > 0, 0)).rolling(7).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(7).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))

    df['volatility'] = df['Close'].rolling(10).std()
    df['vol_mean'] = df['Volume'].rolling(10).mean()

    return df

# =========================
# ESTRATÉGIA INSANA
# =========================
def analyze(df):
    try:
        df = indicators(df)
        df.dropna(inplace=True)

        if len(df) < 30:
            return None

        last = df.iloc[-1]
        prev = df.iloc[-2]

        signal = None
        score = 0

        # TENDÊNCIA
        if last['ema9'] > last['ema21']:
            trend = "UP"
            score += 1
        else:
            trend = "DOWN"
            score += 1

        # MOMENTO
        if trend == "UP" and last['rsi'] < 75:
            signal = "COMPRA"
            score += 1
        elif trend == "DOWN" and last['rsi'] > 25:
            signal = "VENDA"
            score += 1

        # VOLUME
        if last['Volume'] > last['vol_mean']:
            score += 1

        # VOLATILIDADE
        if last['volatility'] > df['volatility'].mean():
            score += 1

        # FORÇA MOVIMENTO
        movement = abs(last['Close'] - prev['Close']) / prev['Close']
        if movement > 0.001:
            score += 1

        if signal is None:
            return None

        # CONFIANÇA
        confidence = 0.40 + (score * 0.1)

        if confidence < 0.45:
            return None

        # =========================
        # STOP E ALVO
        # =========================
        entry = last['Close']

        if signal == "COMPRA":
            stop = entry * 0.98
            target = entry * 1.03
        else:
            stop = entry * 1.02
            target = entry * 0.97

        return signal, confidence, entry, stop, target

    except Exception as e:
        print(f"Erro análise: {e}")
        return None

# =========================
# LOOP
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
⚡ Modo: Agressivo Profissional
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
