# trend_classifier.py
import yfinance as yf
import pandas as pd


def classify_trend(ticker):

    data = yf.download(ticker, period="6mo")['Close']
    if data.empty:
        return "Нет данных для классификации тренда."

    if isinstance(data, pd.DataFrame):
        data = data.iloc[:, 0]
    ema12 = data.ewm(span=12, adjust=False).mean()
    ema26 = data.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    last_macd = float(macd.iloc[-1])

    if last_macd > 0:
        trend = "📈 Бычий рынок (восходящий тренд)"
    elif last_macd < 0:
        trend = "📉 Медвежий рынок (нисходящий тренд)"
    else:
        trend = "Нейтральный тренд"

    return f"{trend} (MACD: {last_macd:.2f})"
