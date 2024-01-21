import ccxt
import pandas as pd
from ta.trend import ema_indicator
import asyncio
import nest_asyncio
from telegram import Bot
from plyer import notification

# Binance API credentials
api_key = 'BVhb32XgQmX17IGs3vVH2Hw1fiH9W84pg8K5JtLuQnRKHPy7YlyPTG0qChkxTnrL'
api_secret = 'xVM8dF8qIhTRtfaTShbHON7oJffooUbP2wp3oPqYUbFLJ1ZCHLN9dEmN9niAYzVF'
interval = '1d'  # 1-hour candlesticks

# Telegram Bot Token and Chat ID
telegram_token = '6811110812:AAFNJp5kcSh0KZ71Yizf8Y3rPBarz-ywopM'
chat_id = '1385370555'

# Initialize Binance client
binance = ccxt.binance({
    'apiKey': api_key,
    'secret': api_secret,
})


# Dictionary to store the last alert messages for each symbol
last_alert_messages = {}

# Function to get historical candlestick data
def get_historical_data(symbol, interval, limit=100):
    ohlcv = binance.fetch_ohlcv(symbol, interval, limit=limit)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    return df

# Function to check EMA cross
def check_ema_cross(df, short_period=12, long_period=26):
    df['ema_short'] = ema_indicator(df['close'], window=short_period)
    df['ema_long'] = ema_indicator(df['close'], window=long_period)

    cross_over = df['ema_short'][-1] > df['ema_long'][-1] and df['ema_short'][-2] <= df['ema_long'][-2]
    cross_under = df['ema_short'][-1] < df['ema_long'][-1] and df['ema_short'][-2] >= df['ema_long'][-2]

    return cross_over, cross_under

# Function to send Telegram message (now defined as async)
async def send_telegram_message(symbol, message):
    # Check if the current message is the same as the previous one for this symbol
    if last_alert_messages.get(symbol) != message:
        await telegram_bot.send_message(chat_id=chat_id, text=message)
        notification.notify(
            title='EMA Cross Alert',
            message=message,
        )
        # Update the last alert message for this symbol
        last_alert_messages[symbol] = message

# Main function (now defined as async)
async def main():
    # Get all trading pairs on Binance
    all_trading_pairs = binance.fetch_markets()

    while True:
        for trading_pair in all_trading_pairs:
            symbol = trading_pair['symbol']
            # Filter only spot trading pairs with USDT as the quote currency
            if trading_pair['type'] == 'spot' and trading_pair['quote'] == 'USDT':
                try:
                    historical_data = get_historical_data(symbol, interval)
                    cross_over, cross_under = check_ema_cross(historical_data)

                    if cross_over:
                        message = f'EMA Cross Over detected on {symbol} ({interval}).'
                        await send_telegram_message(symbol, message)

                    if cross_under:
                        message = f'EMA Cross Under detected on {symbol} ({interval}).'
                        await send_telegram_message(symbol, message)

                except Exception as e:
                    print(f"Error processing {symbol}: {e}")

        # Sleep for a specified interval before checking again
        await asyncio.sleep(1)  # Adjust the sleep duration as needed

# Initialize Telegram Bot
telegram_bot = Bot(token=telegram_token)

# Use nest_asyncio to allow running asyncio in Jupyter notebooks
nest_asyncio.apply()

# Create and run the event loop
asyncio.run(main())
