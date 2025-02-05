import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from sklearn.preprocessing import MinMaxScaler
import yfinance as yf
from config import LSTM_EPOCHS, LSTM_BATCH_SIZE

def predict_stock_price(ticker):
    """Прогнозирует цену на следующий день с помощью LSTM."""
    data = yf.download(ticker, period="2y")['Close']
    if data.empty or len(data) < 61:
        raise ValueError(f"Недостаточно данных для прогнозирования для {ticker}.")

    data = data.values.reshape(-1, 1)
    scaler = MinMaxScaler(feature_range=(0, 1))
    data_scaled = scaler.fit_transform(data)

    X, y = [], []
    sequence_length = 60
    for i in range(sequence_length, len(data_scaled)):
        X.append(data_scaled[i-sequence_length:i, 0])
        y.append(data_scaled[i, 0])

    X, y = np.array(X), np.array(y)
    X = X.reshape((X.shape[0], X.shape[1], 1))

    # Создаем модель LSTM
    model = Sequential([
        LSTM(50, return_sequences=True, input_shape=(X.shape[1], 1)),
        LSTM(50, return_sequences=False),
        Dense(25),
        Dense(1)
    ])
    model.compile(optimizer='adam', loss='mean_squared_error')
    model.fit(X, y, batch_size=LSTM_BATCH_SIZE, epochs=LSTM_EPOCHS, verbose=0)

    last_60_days = data_scaled[-sequence_length:].reshape(1, sequence_length, 1)
    predicted_price_scaled = model.predict(last_60_days)
    predicted_price = scaler.inverse_transform(predicted_price_scaled)

    return predicted_price[0][0]
