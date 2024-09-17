# working strategy in real time uses rsi and moving average. buy when 9ma>12ma>20ma and 50<rsi<60 sell 9ma<12ma or 20% # #increase



import os
import requests
import json
import time
import csv
from datetime import datetime, timedelta
import pandas as pd
import talib

def fetch_current_price(retry_delay=1.5):
    url = "https://public-api.birdeye.so/public/price?address=replace with your key"
    headers = {"X-API-KEY": "replace with your key"}

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
            time.sleep(retry_delay)

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

def generate_signals(df, position, last_buy_timestamp):
    # Drop rows with NaN values in the 'close' column
    df = df.dropna(subset=['close'])

    # Calculate RSI
    df['rsi'] = talib.RSI(df['close'], timeperiod=14)

    # Calculate Bollinger Bands
    df['upper_band'], df['middle_band'], df['lower_band'] = talib.BBANDS(df['close'], timeperiod=20, nbdevup=2,
                                                                         nbdevdn=2)

    # Create columns for short-term and long-term moving averages
    df['short_ma'] = df['close'].rolling(window=12).mean()
    df['medium_ma'] = df['close'].rolling(window=15).mean()
    df['long_ma'] = df['close'].rolling(window=9).mean()

    # Generate signals based on modified conditions
    if position == 'buy':
        # Buy conditions
        print("rsi", df['rsi'].iloc[-1])
        print("long_ma 9 ma", df['long_ma'].iloc[-1])
        print("medium_ma 15 ma", df['medium_ma'].iloc[-1])
        print("short_ma 12 ma", df['short_ma'].iloc[-1])
        print("slope", df['medium_ma'].diff(5).gt(0).all())
        buy_conditions = (df['rsi'] < 60) & (df['rsi'] > 50) & (df['long_ma'] > df['short_ma']) & \
                          (df['short_ma'] > df['medium_ma'])

        df['buy_signal'] = buy_conditions
        df['sell_signal'] = False

        # Update the last_buy_timestamp when a new buy signal is generated
        if df['buy_signal'].any():
            last_buy_timestamp = df.loc[df['buy_signal'], 'timestamp'].max()

    elif position == 'sell':
        df['buy_signal'] = False
        # Sell conditions
        df['sell_signal'] = (df['close'] > df['close'].shift(1) * 1.2) | (df['long_ma'] < df['short_ma'] )| (df['rsi'] < 50)


    return df, last_buy_timestamp

if __name__ == "__main__":
    try:
        csv_filename = 'EURUSD_Candlestick_14s_ASK_30.09.2019-30.09.2022.csv'

        df = pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close'])
        # write_to_csv(csv_filename, df)
        position = 'buy'  # Initial position
        last_buy_timestamp = None
        buy_index=0
        sell_index=0

        while True:
            start_time = datetime.now()

            ohlc_data = None

            # Collect data for 14 seconds
            while (datetime.now() - start_time).total_seconds() < 14:
                current_price = fetch_current_price()
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

            # Set open price to the first tick's price
            ohlc_data['open'] = ohlc_data['close']

            # Write to CSV
            write_to_csv(csv_filename, ohlc_data)

            # Create DataFrame from CSV file
            df = pd.read_csv(csv_filename)

            # Generate signals and print buy and sell signals
            df, last_buy_timestamp = generate_signals(df, position, last_buy_timestamp)

            buy_signals = df.loc[df['buy_signal'], 'timestamp'].tolist()
            sell_signals = df.loc[df['sell_signal'], 'timestamp'].tolist()
            df_copy = df.iloc[sell_index:].copy()

            sell_signals2 = df_copy.loc[df_copy['sell_signal'], 'timestamp'].tolist()


            try:
                    # sell_index = df_copy[df_copy['sell_signal'].first_valid_index()].index
                sell_index = df_copy.loc[df_copy['buy_signal']].last_valid_index().item()

            except AttributeError:
                print("no neew buy signals")



            #buy_index = df_copy.index[df_copy['buy_signal'].first_valid_index()]

            buy_signals_trim = [df_copy.loc[df_copy['buy_signal'], 'timestamp'].min()]
            sell_signals_trim = [df_copy.loc[df_copy['sell_signal'], 'timestamp'].min()]

            buy_signals_trim_list = []
            min_buy_timestamp = df_copy.loc[df_copy['buy_signal'], 'timestamp'].min()
            if not pd.isna(min_buy_timestamp):  # Check if there are valid values
                buy_signals_trim_list.append(min_buy_timestamp)

            sell_signals_trim_list = []

            # Assuming df_copy is your DataFrame
            min_sell_timestamp = df_copy.loc[df_copy['sell_signal'], 'timestamp'].min()
            if not pd.isna(min_sell_timestamp):  # Check if there are valid values
                sell_signals_trim_list.append(min_sell_timestamp)


            if position == 'buy' and buy_signals:
                print("Buy Signals original:")
                print(buy_signals)
                print("Buy Signals trim:")
                print(buy_signals_trim_list)
                position = 'sell'  # Change position to 'sell' after a buy signal

            if position == 'sell' and sell_signals:
                print("Sell Signals:")
                print(sell_signals)
                print("Sell Signals trim:")
                print(sell_signals_trim_list)
                position = 'buy'  # Change position to 'buy' after a sell signal

    except KeyboardInterrupt:
        print("Program stopped.")
