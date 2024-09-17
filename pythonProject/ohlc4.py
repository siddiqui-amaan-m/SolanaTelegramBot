# add emergency stop when two values of ohlc data are same



import os
import requests
import json
import time
import csv
from datetime import datetime, timedelta
import pandas as pd
import talib
import numpy as np
from typing import Final
from telethon.sync import TelegramClient, events

TOKEN: Final = '6860242707:AAEbmSXpAY08sUmtKOqvb-wjO2cNQuMvvCM'
BOT_USERNAME: Final = '@readbirdeye_bot'

phone = '+919949604746'
username = 'Xhvv'
API_ID = '22072625'
API_HASH = '026474923fd20d447085bd6dc4cd939f'
global user_address

def get_user_input():
    address = input("Enter Address: ")
    return address


def fetch_current_price(user_address):

    url = "https://public-api.birdeye.so/public/price?address="+user_address
    headers = {"X-API-KEY": "bd7ce1e488d54b3fa341214f4aeb295c"}

    while True:
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)
            parsed_data = json.loads(response.text)

            if parsed_data.get('success', False):
                return parsed_data['data']['value']
            else:
                print("Error: Success is not True in the response.")
                return None

        except requests.RequestException as e:
            print(f"Error fetching price data: {e}")
            time.sleep(1.5)


def format_ohlc(tick_data):
    # Assume tick_data is a float representing the tick price
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return {'timestamp': timestamp, 'open': tick_data, 'high': tick_data, 'low': tick_data, 'close': tick_data}

def write_to_csv(csv_filename, data):
    fieldnames = ['timestamp', 'open', 'high', 'low', 'close']

    # Check if the file is empty
    is_empty = not os.path.isfile(csv_filename) or os.stat(csv_filename).st_size == 0

    with open(csv_filename, 'a', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Write the header if the file is empty
        if is_empty:
            writer.writeheader()

        writer.writerow(data)


def buy_send_message(message_text):
        try:
            # Find the channel entity
            CHANNEL_USERNAME = '-1001854688903'
            CHANNEL_USERNAME2 = '-1002097266372'
            token = '6860242707:AAEbmSXpAY08sUmtKOqvb-wjO2cNQuMvvCM'
            url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={CHANNEL_USERNAME}&text={message_text}"
            url2 = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={CHANNEL_USERNAME2}&text={user_address}"

            response = requests.post(url)
            response2 = requests.post(url2)

            if response.status_code == 200 | response2.status_code == 200:
                print(f"Buy message sent successfully")
            else:
                print(f"Error sending message: {response.status_code}")
                print(f"Error sending message: {response2.status_code}")
        except Exception as e:
            print(f"Error sending Buy message: {e}")

def sell_send_message(message_text):
        try:
            # Find the channel entity
            CHANNEL_USERNAME = '-1001854688903'
            CHANNEL_USERNAME2 = '-1002044138543'

            token = '6860242707:AAEbmSXpAY08sUmtKOqvb-wjO2cNQuMvvCM'
            url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={CHANNEL_USERNAME}&text={message_text}"
            url2 = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={CHANNEL_USERNAME2}&text={user_address}"

            response = requests.post(url)
            response2 = requests.post(url2)

            if response.status_code == 200 | response2.status_code == 200:
                print(f"Sell message sent successfully")
            else:
                print(f"Error sending message: {response.status_code}")
                print(f"Error sending message: {response2.status_code}")
        except Exception as e:
            print(f"Error sending Sell message: {e}")



def identify_candlestick_patterns(df):
    # Identify candlestick patterns
    bullish_engulfing = (df['open'].shift(1) > df['close'].shift(1)) & (df['close'] > df['open']) & \
                        (df['close'] > df['open'].shift(1)) & (df['open'] < df['close'].shift(1))

    bearish_engulfing = (df['open'].shift(1) < df['close'].shift(1)) & (df['close'] < df['open']) & \
                        (df['close'] < df['open'].shift(1)) & (df['open'] > df['close'].shift(1))

    hammer = (df['close'] > df['open']) & (df['low'] < df['open'] - 0.5 * (df['high'] - df['open'])) & \
             (df['close'] == df['high'])

    # Return True if any of the patterns are identified for each row
    return bullish_engulfing | bearish_engulfing | hammer

import talib

def generate_signals(df, last_buy_timestamp, last_sell_timestamp, prev_signal, reset_time):
    # Drop rows with NaN values in the 'close' column
    df = df.dropna(subset=['close'])

    # Calculate SuperTrend indicators with different parameters
    df['supertrend_11_2'] = talib.SMA(df['close'], timeperiod=11) + (talib.ATR(df['high'], df['low'], df['close'], timeperiod=11) * 2)

    # Define buy conditions based on SuperTrend indicators
    df['ema_50'] = talib.SMA(df['close'], timeperiod=50).mean()
    df['medium_ma'] = df['close'].ewm(span=15, adjust=False).mean()
    df['long_ma'] = df['close'].ewm(span=5, adjust=False).mean()
    df['rsi'] = talib.RSI(df['close'], timeperiod=14)

    # Define buy conditions based on SuperTrend and 50 EMA
    buy_conditions = (df['supertrend_11_2'] > df['ema_50']) & ('sell_signal' not in df.columns or df['sell_signal'].astype(bool).sum() == 0)
    df['buy_signal'] = buy_conditions
    # Define sell conditions based on SuperTrend indicators
    df['sell_signal'] = (df['long_ma'] < df['medium_ma'])
    if df['buy_signal'].iloc[-1]:
        new_buy_timestamp = df.loc[df['buy_signal'], 'timestamp'].max()
        if last_sell_timestamp is None or (new_buy_timestamp > last_sell_timestamp):
            if prev_signal != "buy":
                last_buy_timestamp = pd.to_datetime(new_buy_timestamp)
                print("Buy Signal:", last_buy_timestamp)



                import datetime
                current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                price = fetch_current_price(user_address)
                # Create the string

                prev_signal = "buy"

        # Sell conditions

    df['sell_signal'] = (df['long_ma'] < df['medium_ma']) | (df['rsi'] < 45)

    # Apply the condition to check if the sell timestamp is greater than the last buy timestamp
    df['sell_signal'] = df['sell_signal'] & (pd.to_datetime(df['timestamp']) > last_buy_timestamp)

    if df['sell_signal'].any():
        new_sell_timestamp = df.loc[df['sell_signal'], 'timestamp'].max()
        if last_sell_timestamp is None or new_sell_timestamp > last_sell_timestamp:
            if prev_signal != "sell":
                last_sell_timestamp = new_sell_timestamp
                print("Sell Signal:", last_sell_timestamp)

                prev_signal = "sell"
                price = fetch_current_price(user_address)
                # Calculate the current time
                import datetime
                current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')



    df.to_csv('output.csv')
    return df, last_buy_timestamp, last_sell_timestamp, prev_signal, reset_time





if __name__ == "__main__":
    try:
        csv_filename = 'EURUSD_Candlestick_14s_ASK_30.09.2019-30.09.2022.csv'

        df = pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close'])
        # write_to_csv(csv_filename, df)

        prev_signal = "buy" # Initial position
        last_buy_timestamp = datetime.min
        last_sell_timestamp = None
        prev_ohlc_data = None
        reset_time = datetime.min

        try:
            os.remove(csv_filename)
            print(f"Deleted {csv_filename}")
        except FileNotFoundError:
            pass

        try:
            os.remove('output.csv')
            print("Deleted output.csv")
        except FileNotFoundError:
            pass

        user_address = get_user_input()
        while True:
            start_time = datetime.now()

            ohlc_data = None

            # Prompt user for address and pass it to fetch_current_price

            # Collect data for 14 seconds
            while (datetime.now() - start_time).total_seconds() < 10:
                current_price = fetch_current_price(user_address)
                if current_price is not None:
                    if ohlc_data is None:
                        ohlc_data = format_ohlc(current_price)
                    else:
                        ohlc_data['high'] = max(ohlc_data['high'], current_price)
                        ohlc_data['low'] = min(ohlc_data['low'], current_price)
                        ohlc_data['close'] = current_price

                    # Print or use the OHLC data as needed
                    # print("OHLC Data:", ohlc_data)

                time.sleep(2)  # Wait for 2 seconds before the next iteration

            if ohlc_data is not None:
                # Set open price to the first tick's price
                ohlc_data['open'] = ohlc_data['close']

            if prev_ohlc_data is not None and ohlc_data.equals(prev_ohlc_data):
                print("Trading bot stopped due to low price activity.")
                buy_send_message("Trading bot stopped due to low price activity.")
                sell_send_message("Trading bot stopped due to low price activity.")
                break

            # Write to CSV
            write_to_csv(csv_filename, ohlc_data)

            # Create DataFrame from CSV file
            df = pd.read_csv(csv_filename)

            # Generate signals and print buy and sell signals
            df, last_buy_timestamp, last_sell_timestamp, prev_signal, reset_time = generate_signals(df, last_buy_timestamp, last_sell_timestamp, prev_signal, reset_time)

            #buy_signals = df.loc[df['buy_signal'], 'timestamp'].tolist()
            #sell_signals = df.loc[df['sell_signal'], 'timestamp'].tolist()

              # Change position to 'buy' after a sell signal

    except KeyboardInterrupt:
        print("Program stopped.")

        try:
            os.remove(csv_filename)
            print(f"Deleted {csv_filename}")
        except FileNotFoundError:
            pass

        try:
            os.remove('output.csv')
            print("Deleted output.csv")
        except FileNotFoundError:
            pass