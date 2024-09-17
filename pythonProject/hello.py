# add emergency stop when two values of ohlc data are same



import os
import threading

import requests
import json
import time
import csv
from datetime import datetime, timedelta
import pandas as pd
import talib
from typing import Final
from telethon.sync import TelegramClient, events

BOT_TOKEN: Final = '6860242707:replace with your key-replace with your key'
BOT_USERNAME: Final = '@replace with your key'

phone = '+replace with your key'
username = 'replace with your key'
API_ID = 'replace with your key'
API_HASH = 'replace with your key'


import telebot


bot = telebot.TeleBot(BOT_TOKEN)
user_address = None
running = True  # Flag to indicate bot's running state

@bot.message_handler(commands=['start'])
def start_bot(message):
    try:
        global running
        if running:
            bot.reply_to(message, "Bot is already running.")
        else:
            running = True
            bot.reply_to(message, "Bot started successfully!")




            global csv_filename
            csv_filename= 'EURUSD_Candlestick_14s_ASK_30.09.2019-30.09.2022.csv'

            df = pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close'])
            # write_to_csv(csv_filename, df)

            prev_signal = "buy"  # Initial position
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


            while running:
                if user_address is None:
                    bot.send_message(message.chat.id, "User address is not set. Stopping the loop.")
                    break
                if message.text.lower() == '/stop':
                    stop_bot(message.chat.id)
                    break

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


                ''''
                if prev_ohlc_data is not None :
                    check = are_dicts_equal_except_first(prev_ohlc_data, ohlc_data)
                    if check==True:
                        print("Trading bot stopped due to low price activity.")
                        buy_send_message("Trading bot stopped due to low price activity.")
                        sell_send_message("Trading bot stopped due to low price activity.")
                        running = False
                        stop_bot(message)
                        break'''

                # Write to CSV
                write_to_csv(csv_filename, ohlc_data)
                prev_ohlc_data = ohlc_data
                # Create DataFrame from CSV file
                df = pd.read_csv(csv_filename)

                # Generate signals and print buy and sell signals
                df, last_buy_timestamp, last_sell_timestamp, prev_signal, reset_time = generate_signals(df,
                                                                                                        last_buy_timestamp,
                                                                                                        last_sell_timestamp,
                                                                                                        prev_signal,
                                                                                                        reset_time, user_address)

                buy_signals = df.loc[df['buy_signal'], 'timestamp'].tolist()
                sell_signals = df.loc[df['sell_signal'], 'timestamp'].tolist()

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


def are_dicts_equal_except_first(dict1, dict2):
    # Check if the keys are the same
    if set(dict1.keys()) != set(dict2.keys()):
        return False

    # Check if the values for each key (except the first one) are the same
    keys = list(dict1.keys())[1:]  # Exclude the first key
    for key in keys:
        if dict1[key] != dict2[key]:
            return False

    return True

@bot.message_handler(commands=['address'])
def address_handler(message):
    try:
        # Prompt the user to enter their address
        if running == False:
            bot.send_message(message.chat.id, "Please enter your address:")
        # Register a message handler for the next message in the same chat
            bot.register_next_step_handler(message, process_address_input)
        else:
            bot.send_message(message.chat.id, f"Stop the bot first before changing the address")
            bot.send_message(message.chat.id, f"Current address is: {user_address}")
    except Exception as e:
        bot.reply_to(message, f"An error occurred: {e}")

def process_address_input(message):
    global user_address
    try:
        user_address = message.text
        bot.send_message(message.chat.id, f"Address set to: {user_address}")
    except Exception as e:
        bot.reply_to(message, f"An error occurred: {e}")


@bot.message_handler(commands=['stop'])
def stop_bot(message):
    global running
    if not running:
        bot.reply_to(message, "Bot is already stopped.")
    else:

        running = False
        bot.reply_to(message, "Bot stopped successfully.")
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
                print(f"Sell message sent successfully")
            else:
                print(f"Error sending message: {response.status_code}")
                print(f"Error sending message: {response2.status_code}")
            # Send the message
            '''client.send_message(entity, message_text)
            print("Buy message sent successfully.")'''
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
            # Send the message
            '''client.send_message(entity, message_text)
            print("Sell message sent successfully.")'''
        except Exception as e:
            print(f"Error sending Sell message: {e}")

def generate_signals(df, last_buy_timestamp, last_sell_timestamp, prev_signal, reset_time, user_address):
    # Drop rows with NaN values in the 'close' column
    # Drop rows with NaN values in the 'close' column
    df = df.dropna(subset=['close'])

    # Calculate RSI
    df['rsi'] = talib.RSI(df['close'], timeperiod=14)

    # Calculate Bollinger Bands
    df['upper_band'], df['middle_band'], df['lower_band'] = talib.BBANDS(df['close'], timeperiod=20, nbdevup=2,
                                                                         nbdevdn=2)

    # Create columns for short-term and long-term moving averages
    df['short_ma'] = df['close'].ewm(span=10, adjust=False).mean()
    #df['medium_ma'] = talib.SMA(df['close'], timeperiod=13)
    df['medium_ma'] = df['close'].ewm(span=13, adjust=False).mean()
    df['long_ma'] = df['close'].ewm(span=5, adjust=False).mean()

    percent=0
    try:
        last_rsi = df['rsi'].iloc[-1]
        second_last_rsi = df['rsi'].iloc[-4]
        percent = ((last_rsi - second_last_rsi) / second_last_rsi) * 100
        if percent>24:
            import datetime
            reset_time = datetime.datetime.now()

    except IndexError:
        print("Not enough rows in the DataFrame.")

    # Generate signals based on modified conditions i changed medium ma from simple to exp
    #keep percentage 9 to have allowed gain from 55 to 60 & (percent<8) rsi was between 60 and 67

    # Buy conditions
    import datetime
    current_time = datetime.datetime.now()
    is_greater_than_4_minutes = (current_time - reset_time) > timedelta(minutes=4)

    buy_conditions = (is_greater_than_4_minutes == True)  & (df['rsi'] < 200) & (df['rsi'] > 60) & (df['long_ma'] > df['short_ma']) & \
                     (df['short_ma'] > df['medium_ma']) & \
                     ('sell_signal' not in df.columns or df['sell_signal'].astype(bool).sum() == 0)

    df['buy_signal'] = buy_conditions

    # Update the last_buy_timestamp when a new buy signal is generated
    if df['buy_signal'].iloc[-1]:
        new_buy_timestamp = df.loc[df['buy_signal'], 'timestamp'].max()
        if last_sell_timestamp is None or (new_buy_timestamp > last_sell_timestamp):
            if prev_signal!="buy":
                last_buy_timestamp = pd.to_datetime(new_buy_timestamp)
                print("Buy Signal:", last_buy_timestamp)
                import datetime
                current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                price = fetch_current_price(user_address)
                # Create the string
                message = f"Current price is {price},\nCurrent time is {current_time}, buy order from laptop submitted"
                buy_send_message(message)
                prev_signal="buy"



        # Sell conditions

    df['sell_signal'] = (df['long_ma'] < df['medium_ma']) | (df['rsi'] < 45)

    # Apply the condition to check if the sell timestamp is greater than the last buy timestamp
    df['sell_signal'] = df['sell_signal'] & (pd.to_datetime(df['timestamp']) > last_buy_timestamp)

    if df['sell_signal'].any():
        new_sell_timestamp = df.loc[df['sell_signal'], 'timestamp'].max()
        if last_sell_timestamp is None or new_sell_timestamp > last_sell_timestamp:
            if prev_signal!="sell":
                last_sell_timestamp = new_sell_timestamp
                print("Sell Signal:", last_sell_timestamp)
                prev_signal = "sell"
                price = fetch_current_price(user_address)
                # Calculate the current time
                import datetime
                current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                # Create the string
                message = f"Current price is {price},\nCurrent time is {current_time}, sell order from laptop submitted"
                sell_send_message(message)

    df.to_csv('output.csv')

    return df, last_buy_timestamp, last_sell_timestamp, prev_signal, reset_time




if __name__ == "__main__":
    try:
        running = False
        bot.polling()
        #while True:
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