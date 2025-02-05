from datetime import time
import threading
import schedule
from config import TICKERS
from utils import get_token
from analysis import analyze_stock
from ml_forecast import predict_stock_price
from chart import send_stock_chart, send_extended_chart
from trend_classifier import classify_trend
import telebot
import logging
import pandas as pd

api_allowed = {}
pending_indicators = {}

def reset_api_flag(chat_id):
    api_allowed[chat_id] = True
    return schedule.CancelJob

def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

threading.Thread(target=run_schedule, daemon=True).start()
logging.basicConfig(level=logging.INFO)
bot = telebot.TeleBot(get_token())
pending_analysis = {}
pending_chart = {}

def get_ticker_keyboard():
    keyboard = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    buttons = [telebot.types.KeyboardButton(ticker) for ticker in TICKERS]
    keyboard.add(*buttons)
    return keyboard

@bot.message_handler(commands=['indicators'])
def start_indicators(message):
    chat_id = message.chat.id
    pending_indicators[chat_id] = "waiting_for_ticker"
    bot.send_message(chat_id, "Выберите тикер для детального технического анализа:", reply_markup=get_ticker_keyboard())

@bot.message_handler(func=lambda message: message.text in TICKERS and message.chat.id in pending_indicators and pending_indicators[message.chat.id] == "waiting_for_ticker")
def select_indicators_ticker(message):
    chat_id = message.chat.id
    ticker = message.text
    pending_indicators[chat_id] = ticker
    period_keyboard = telebot.types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    period_buttons = [telebot.types.KeyboardButton(p) for p in ["1m", "3m", "6m", "1y", "5y"]]
    period_buttons.append(telebot.types.KeyboardButton("Назад"))
    period_keyboard.add(*period_buttons)
    bot.send_message(chat_id, f"Тикер *{ticker}* выбран.\nВыберите временной диапазон для детального анализа:", parse_mode='Markdown', reply_markup=period_keyboard)

@bot.message_handler(func=lambda message: message.text == "Назад" and message.chat.id in pending_indicators)
def indicators_go_back(message):
    chat_id = message.chat.id
    pending_indicators[chat_id] = "waiting_for_ticker"
    bot.send_message(chat_id, "Возвращаемся к выбору тикера:", reply_markup=get_ticker_keyboard())

@bot.message_handler(func=lambda message: message.text in ["1m", "3m", "6m", "1y", "5y"] and message.chat.id in pending_indicators and pending_indicators[message.chat.id] != "waiting_for_ticker")
def select_indicators_period(message):
    chat_id = message.chat.id
    period = message.text
    ticker = pending_indicators.pop(chat_id)
    bot.send_message(chat_id, f"Получение детальных технических индикаторов для *{ticker}* за период *{period}*...", parse_mode='Markdown', reply_markup=get_ticker_keyboard())
    try:
        data = analyze_stock(ticker, period)
        close = data["Close"]
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]
        rsi = data['RSI_14'].iloc[-1]
        sma50 = data['SMA_50'].iloc[-1]
        sma200 = data['SMA_200'].iloc[-1]
        sma20 = data['SMA_20'].iloc[-1]
        bb_upper = data['BB_Upper'].iloc[-1]
        bb_lower = data['BB_Lower'].iloc[-1]
        macd = data['MACD'].iloc[-1]
        indicators_text = (
            f"📊 *Детальные технические индикаторы для {ticker}*:\n"
            f"• *RSI (14)*: {rsi:.2f}\n"
            f"• *SMA 50*: ${sma50:.2f}\n"
            f"• *SMA 200*: ${sma200:.2f}\n"
            f"• *SMA 20*: ${sma20:.2f}\n"
            f"• *BB Верхняя*: ${bb_upper:.2f}\n"
            f"• *BB Нижняя*: ${bb_lower:.2f}\n"
            f"• *MACD*: {macd:.2f}"
        )
        bot.send_message(chat_id, indicators_text, parse_mode='Markdown')
    except Exception as e:
        logging.exception("Ошибка при получении технических индикаторов")
        bot.send_message(chat_id, f"Ошибка: {str(e)}")

@bot.message_handler(commands=['start'])
def start_analysis(message):
    chat_id = message.chat.id
    if chat_id in pending_chart:
        pending_chart.pop(chat_id)
    pending_analysis[chat_id] = "waiting_for_ticker"
    bot.send_message(chat_id, "Выберите тикер для анализа:", reply_markup=get_ticker_keyboard())

@bot.message_handler(commands=['chart'])
def start_chart(message):
    chat_id = message.chat.id
    if chat_id in pending_analysis:
        pending_analysis.pop(chat_id)
    pending_chart[chat_id] = "waiting_for_ticker"
    bot.send_message(chat_id, "Выберите тикер для построения расширенного графика:", reply_markup=get_ticker_keyboard())

@bot.message_handler(func=lambda message: message.text == "Назад")
def go_back(message):
    chat_id = message.chat.id
    if chat_id in pending_analysis:
        pending_analysis[chat_id] = "waiting_for_ticker"
        bot.send_message(chat_id, "Возвращаемся к выбору тикера для анализа:", reply_markup=get_ticker_keyboard())
    elif chat_id in pending_chart:
        pending_chart[chat_id] = "waiting_for_ticker"
        bot.send_message(chat_id, "Возвращаемся к выбору тикера для построения графика:", reply_markup=get_ticker_keyboard())
    else:
        pending_analysis[chat_id] = "waiting_for_ticker"
        bot.send_message(chat_id, "Возвращаемся к выбору тикера для анализа:", reply_markup=get_ticker_keyboard())

@bot.message_handler(func=lambda message: message.text in TICKERS)
def process_ticker(message):
    chat_id = message.chat.id
    ticker = message.text
    if chat_id in pending_chart and pending_chart[chat_id] == "waiting_for_ticker":
        pending_chart[chat_id] = ticker
        period_keyboard = telebot.types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
        period_buttons = [telebot.types.KeyboardButton(p) for p in ["1m", "6m", "1y"]]
        period_buttons.append(telebot.types.KeyboardButton("Назад"))
        period_keyboard.add(*period_buttons)
        bot.send_message(chat_id, f"Тикер {ticker} выбран для расширенного графика.\nВыберите период:", reply_markup=period_keyboard)
    elif chat_id in pending_analysis and pending_analysis[chat_id] == "waiting_for_ticker":
        pending_analysis[chat_id] = ticker
        period_keyboard = telebot.types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
        period_buttons = [telebot.types.KeyboardButton(p) for p in ["1m", "3m", "6m", "1y", "5y"]]
        period_buttons.append(telebot.types.KeyboardButton("Назад"))
        period_keyboard.add(*period_buttons)
        bot.send_message(chat_id, f"Тикер {ticker} выбран для анализа.\nВыберите временной диапазон для анализа:", reply_markup=period_keyboard)

@bot.message_handler(func=lambda message: message.text in ["1m", "3m", "6m", "1y", "5y"] and message.chat.id in pending_analysis and pending_analysis[message.chat.id] != "waiting_for_ticker")
def select_analysis_period(message):
    chat_id = message.chat.id
    if not api_allowed.get(chat_id, True):
        bot.send_message(chat_id, "Подождите 10 секунд между запросами.")
        return
    api_allowed[chat_id] = False
    schedule.every(10).seconds.do(reset_api_flag, chat_id)
    period = message.text
    ticker = pending_analysis.pop(chat_id)
    bot.send_message(chat_id, f"🔎 Анализ {ticker} за период {period} запущен. Ожидайте результаты...")
    try:
        data = analyze_stock(ticker, period)
        close = data["Close"]
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]
        if len(close) < 2:
            raise ValueError("Недостаточно данных для расчёта разницы цен.")
        last_price = float(close.iloc[-1])
        prev_close = float(close.iloc[-2])
        price_diff = last_price - prev_close
        percent_change = (last_price / prev_close - 1) * 100
        sign = "+" if price_diff >= 0 else ""
        volatility_warning = ""
        if len(close) >= 14:
            last_14 = close.tail(14)
            avg_deviation = (last_14 - last_14.mean()).abs().mean()
            mean_last14 = last_14.mean()
            relative_volatility = float((avg_deviation / mean_last14) * 100)
            if relative_volatility > 2.0:
                volatility_warning = f"\n⚠️ *Высокая волатильность*: {relative_volatility:.2f}%"
        signal_text = (
            f"📊 *Анализ {ticker}*:\n"
            f"📈 *Цена*: *${last_price:.2f}*\n"
            f"🔺 *Изменение за день*: {sign}{percent_change:.2f}% ({sign}${abs(price_diff):.2f})"
            f"{volatility_warning}"
        )
        bot.send_message(chat_id, signal_text, parse_mode='Markdown')
        predicted_price = predict_stock_price(ticker)
        forecast_text = f"\n🔮 *Прогноз на завтра*: ${predicted_price:.2f}"
        bot.send_message(chat_id, forecast_text, parse_mode='Markdown')
        trend = classify_trend(ticker)
        trend_text = f"\n📊 *Тренд*: {trend}"
        bot.send_message(chat_id, trend_text, parse_mode='Markdown')
        send_stock_chart(ticker, chat_id)
    except Exception as e:
        logging.exception("Ошибка при обработке запроса анализа")
        bot.send_message(chat_id, f"Ошибка: {str(e)}")

@bot.message_handler(func=lambda message: message.text in ["1m", "6m", "1y"] and message.chat.id in pending_chart and pending_chart[message.chat.id] != "waiting_for_ticker")
def select_chart_period(message):
    chat_id = message.chat.id
    period = message.text
    ticker = pending_chart.pop(chat_id)
    bot.send_message(chat_id, f"Построение графика {ticker} за период {period}. Ожидайте...")
    try:
        send_extended_chart(ticker, chat_id, period)
    except Exception as e:
        logging.exception("Ошибка при построении расширенного графика")
        bot.send_message(chat_id, f"Ошибка: {str(e)}")
@bot.message_handler(commands=['help'])
def show_help(message):
    chat_id = message.chat.id
    help_text = (
        "📌 Доступные команды:\n"
        "/start - выбрать тикер для анализа\n"
        "/chart - построить график\n"
        "/forecast - прогноз цены\n"
        "/trend - анализ тренда\n"
        "/indicators - технические показатели\n"
        "/help - показать эту справку"
    )
    bot.send_message(chat_id, help_text)
if __name__ == '__main__':
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        logging.exception("Ошибка в основном цикле polling")
