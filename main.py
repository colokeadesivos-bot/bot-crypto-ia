import yfinance as yf
import pandas as pd
import numpy as np
import time
import requests
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier

TOKEN = "8748500939:AAHAG6DctidBW4fVp2QQWgbiI-7mjWXt0O8"
CHAT_ID = "SEU_CHAT_ID"

def send(msg):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
    except:
        pass

# =========================
# INDICADORES
# =========================
def rsi(df, n=14):
    delta = df['Close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(n).mean()
    avg_loss = loss.rolling(n).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def add_features(df):
    df['rsi'] = rsi(df)
    df['ma9'] = df['Close'].rolling(9).mean()
    df['ma21'] = df['Close'].rolling(21).mean()
    df['vol'] = df['Volume']
    df['ret'] = df['Close'].pct_change()
    df['target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
    df.dropna(inplace=True)
    return df

# =========================
# BACKTEST
# =========================
def backtest(df):
    df['signal'] = 0

    df.loc[(df['rsi'] < 30) & (df['ma9'] > df['ma21']), 'signal'] = 1
    df.loc[(df['rsi'] > 70) & (df['ma9'] < df['ma21']), 'signal'] = -1

    df['strategy'] = df['signal'].shift(1) * df['ret']

    winrate = (df['strategy'] > 0).mean()
    retorno = df['strategy'].sum()
    sharpe = df['strategy'].mean() / (df['strategy'].std() + 1e-9)

    return winrate, retorno, sharpe

# =========================
# MODELOS (ENSEMBLE)
# =========================
def treinar(df):
    cols = ['rsi','ma9','ma21','vol','ret']
    X = df[cols]
    y = df['target']

    m1 = RandomForestClassifier(n_estimators=150)
    m2 = GradientBoostingClassifier()

    m1.fit(X,y)
    m2.fit(X,y)

    return m1, m2

def prever(models, X):
    m1, m2 = models

    p1 = m1.predict_proba(X)[0]
    p2 = m2.predict_proba(X)[0]

    buy = (p1[1] + p2[1]) / 2
    sell = (p1[0] + p2[0]) / 2

    return buy, sell

# =========================
# RISCO
# =========================
def filtro_risco(winrate, sharpe):
    if winrate < 0.53:
        return False
    if sharpe < 0.5:
        return False
    return True

# =========================
# ANALISAR ATIVO
# =========================
def analisar(symbol, nome):
    try:
        df = yf.download(symbol, period="10d", interval="5m")

        if df.empty:
            print("Sem dados", nome)
            return

        df = add_features(df)

        winrate, retorno, sharpe = backtest(df)

        if not filtro_risco(winrate, sharpe):
            print(f"{nome} ignorado (baixa qualidade)")
            return

        models = treinar(df)

        last = df.iloc[-1]
        X = last[['rsi','ma9','ma21','vol','ret']].values.reshape(1,-1)

        buy, sell = prever(models, X)

        signal = "NEUTRO"
        if buy > 0.68:
            signal = "COMPRA"
        elif sell > 0.68:
            signal = "VENDA"

        if signal == "NEUTRO":
            return

        msg = f"""
🚀 FUNDO QUANT BOT

Ativo: {nome}
Preço: {round(last['Close'],2)}

Winrate: {round(winrate*100,2)}%
Sharpe: {round(sharpe,2)}
Retorno: {round(retorno*100,2)}%

IA Compra: {round(buy*100,2)}%
IA Venda: {round(sell*100,2)}%

🔥 SINAL FORTE: {signal}
"""
        print(msg)
        send(msg)

    except Exception as e:
        print("Erro:", e)

# =========================
# LOOP PRINCIPAL
# =========================
while True:
    print("💎 SISTEMA INSTITUCIONAL ATIVO")

    analisar("BTC-USD", "BTCUSDT")
    analisar("ETH-USD", "ETHUSDT")

    time.sleep(300)
