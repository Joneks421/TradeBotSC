# analysis.py
import yfinance as yf
import pandas as pd
import numpy as np


def analyze_stock(ticker, period="1y"):

    period_mapping = {
        "1m": "1mo",
        "3m": "3mo",
        "6m": "6mo",
        "1y": "1y",
        "5y": "5y"
    }
    yf_period = period_mapping.get(period, "1y")

    data = yf.download(ticker, period=yf_period)
    if data.empty:
        raise ValueError(f"Не удалось загрузить данные для тикера {ticker} за период {period}.")


    data['SMA_50'] = data['Close'].rolling(window=50).mean()
    data['SMA_200'] = data['Close'].rolling(window=200).mean()
    data['EMA_50'] = data['Close'].ewm(span=50, adjust=False).mean()


    delta = data['Close'].diff()
    gain = delta.clip(lower=0).rolling(window=14).mean()
    loss = -delta.clip(upper=0).rolling(window=14).mean()

    rs = gain / loss.replace(0, np.nan)
    data['RSI_14'] = 100 - (100 / (1 + rs))
    data['RSI_14'] = data['RSI_14'].fillna(100)


    data['SMA_20'] = data['Close'].rolling(window=20).mean().squeeze()
    std = data['Close'].rolling(window=20).std().squeeze()
    data['BB_Upper'] = data['SMA_20'] + (std * 2)
    data['BB_Lower'] = data['SMA_20'] - (std * 2)


    data['EMA_12'] = data['Close'].ewm(span=12, adjust=False).mean()
    data['EMA_26'] = data['Close'].ewm(span=26, adjust=False).mean()
    data['MACD'] = data['EMA_12'] - data['EMA_26']


    return data
