# perfect working code


import os
import requests
import json
import time
import csv
from datetime import datetime, timedelta
import pandas as pd
import talib
global user_address

def fetch_current_price(retry_delay=1.5):
    url = "https://public-api.birdeye.so/public/price?address="+ user_address
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
    fieldnames = ['timestamp', 'open', 'high', 'low', 'close', 'txns_m5_buys', 'txns_m5_sells', 'volume_m5', 'price_change_m5', 'liquidity_usd', 'liquidity_base', 'liquidity_quote', 'fdv']


    # Check if the file is empty
    is_empty = not os.path.isfile(csv_filename) or os.stat(csv_filename).st_size == 0

    with open(csv_filename, 'a', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Write the header if the file is empty
        if is_empty:
            writer.writeheader()

        writer.writerow(data)

def generate_signals(df, last_buy_timestamp, last_sell_timestamp, prev_signal):
    # Drop rows with NaN values in the 'close' column
    df = df.dropna(subset=['close'])

    # Calculate RSI
    df['rsi'] = talib.RSI(df['close'], timeperiod=14)

    # Calculate Bollinger Bands
    df['upper_band'], df['middle_band'], df['lower_band'] = talib.BBANDS(df['close'], timeperiod=20, nbdevup=2, nbdevdn=2)

    # Create columns for short-term and long-term moving averages
    df['short_ma'] = talib.SMA(df['close'], timeperiod=5)
    #df['medium_ma'] = talib.SMA(df['close'], timeperiod=15)
    df['long_ma'] = talib.SMA(df['close'], timeperiod=20)
    df['volume_ma'] = talib.SMA(df['close'], timeperiod=20)

    #df['short_ma'] = df['close'].ewm(span=20, adjust=False).mean()
    # df['medium_ma'] = talib.SMA(df['close'], timeperiod=15)
    #df['medium_ma'] = df['close'].ewm(span=15, adjust=False).mean()
    #df['long_ma'] = df['close'].ewm(span=5, adjust=False).mean()




    #substitue EMA instead of SMA for volume and check difference in buy signals ***********


    # Generate signals based on modified conditions

    buysell = (df['txns_m5_buys'].iloc[-1] > (1.2*df['txns_m5_sells'].iloc[-1]))

        # Buy conditions (df['rsi'] < 60) & (df['rsi'] > 50) &
    buy_conditions = (buysell == True) & (df['short_ma'] > df['long_ma']) & (df['volume_m5'].iloc[-1] > df['volume_ma']) & \
                          ('sell_signal' not in df.columns or df['sell_signal'].astype(bool).sum() == 0)

    df['buy_signal'] = buy_conditions


        # Update the last_buy_timestamp when a new buy signal is generated
    if df['buy_signal'].any():
        new_buy_timestamp = df.loc[df['buy_signal'], 'timestamp'].max()
        if last_sell_timestamp is None or new_buy_timestamp > last_sell_timestamp:
            if prev_signal!="buy":
                last_buy_timestamp = new_buy_timestamp
                print("Buy Signal:", last_buy_timestamp)
                prev_signal="buy"



        # Sell conditions(df['close'] > df['close'].shift(1) * 1.2) |
    df['sell_signal'] =  (df['short_ma'] < df['long_ma']) | (df['rsi'] < 45)

        # Apply the condition to check if the sell timestamp is greater than the last buy timestamp
    df['sell_signal'] = df['sell_signal'] & (df['timestamp'] > last_buy_timestamp)

    if df['sell_signal'].any():
            new_sell_timestamp = df.loc[df['sell_signal'], 'timestamp'].max()
            if last_sell_timestamp is None or new_sell_timestamp > last_sell_timestamp:
                if prev_signal!="sell":
                    last_sell_timestamp = new_sell_timestamp
                    print("Sell Signal:", last_sell_timestamp)
                    prev_signal = "sell"

    df.to_csv('output.csv')

    return df, last_buy_timestamp, last_sell_timestamp, prev_signal


def extract_data(response_text):
    # Parse JSON data
    data = json.loads(response_text)

    # Extract required values
    txns_m5_buys = data['pairs'][0]['txns']['m5']['buys']
    txns_m5_sells = data['pairs'][0]['txns']['m5']['sells']
    volume_m5 = data['pairs'][0]['volume']['m5']
    price_change_m5 = data['pairs'][0]['priceChange']['m5']
    liquidity_usd = data['pairs'][0]['liquidity']['usd']
    liquidity_base = data['pairs'][0]['liquidity']['base']
    liquidity_quote = data['pairs'][0]['liquidity']['quote']
    fdv = data['pairs'][0]['fdv']

    # Return extracted data
    extracted_data = {
        "txns_m5_buys": txns_m5_buys,
        "txns_m5_sells": txns_m5_sells,
        "volume_m5": volume_m5,
        "price_change_m5": price_change_m5,
        "liquidity_usd": liquidity_usd,
        "liquidity_base": liquidity_base,
        "liquidity_quote": liquidity_quote,
        "fdv": fdv
    }
    return extracted_data


def get_user_input():
    address = input("Enter Address: ")
    return address

if __name__ == "__main__":
    try:
        csv_filename = 'EURUSD_Candlestick_14s_ASK_30.09.2019-30.09.2022.csv'

        df = pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close'])
        # write_to_csv(csv_filename, df)
        prev_signal = None # Initial position
        last_buy_timestamp = None
        last_sell_timestamp = None


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
            data = None
            # Collect data for 14 seconds
            while (datetime.now() - start_time).total_seconds() < 10:
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
            api_url = "https://api.dexscreener.com/latest/dex/tokens/" + user_address
            response = requests.get(api_url)
            data = extract_data((response.text))
            combined_dict = {**ohlc_data, **data}

            # Write to CSV
            write_to_csv(csv_filename, combined_dict)

            # Create DataFrame from CSV file
            df = pd.read_csv(csv_filename)

            # Generate signals and print buy and sell signals
            df, last_buy_timestamp, last_sell_timestamp, prev_signal = generate_signals(df, last_buy_timestamp, last_sell_timestamp, prev_signal)


            buy_signals = df.loc[df['buy_signal'], 'timestamp'].tolist()
            sell_signals = df.loc[df['sell_signal'], 'timestamp'].tolist()

              # Change position to 'buy' after a sell signal

    except KeyboardInterrupt:
        print("Program stopped.")
