# chart.py
import yfinance as yf
import matplotlib.pyplot as plt
import telebot
import io
from utils import get_token

bot = telebot.TeleBot(get_token())

def send_stock_chart(ticker, chat_id):
    data = yf.download(ticker, period="1d", interval="1h")
    if data.empty:
        bot.send_message(chat_id, f'Не удалось получить данные для построения графика {ticker}.')
        return

    plt.figure(figsize=(10, 5))
    plt.plot(data.index, data['Close'], label=f'{ticker} Price', color='blue')
    plt.title(f'{ticker} - Динамика за 24 часа')
    plt.xlabel('Время')
    plt.ylabel('Цена')
    plt.legend()
    plt.grid()
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    bot.send_photo(chat_id, buf)

def send_extended_chart(ticker, chat_id, period):

    period_mapping = {
        "1m": "1mo",
        "6m": "6mo",
        "1y": "1y"
    }
    yf_period = period_mapping.get(period, "1y")
    data = yf.download(ticker, period=yf_period, interval="1d")
    if data.empty:
        bot.send_message(chat_id, f'Не удалось получить данные для построения графика {ticker} за выбранный период.')
        return

    plt.figure(figsize=(10, 5))
    plt.plot(data.index, data['Close'], label=f'{ticker} Price', color='blue')
    plt.title(f'{ticker} - Динамика за {period}')
    plt.xlabel('Дата')
    plt.ylabel('Цена')
    plt.legend()
    plt.grid()
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    bot.send_photo(chat_id, buf)
