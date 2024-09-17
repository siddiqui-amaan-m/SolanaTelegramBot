import requests
import json
import time
import csv
from datetime import datetime, timedelta

def fetch_current_price(retry_delay=1.5):
    url = "https://public-api.birdeye.so/public/price?address=8wXtPeU6557ETkp9WHFY1n1EcU6NxDvbAggHGsMYiHsB"
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
    with open(csv_filename, 'a', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writerow(data)

if __name__ == "__main__":
    try:
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
                    print("OHLC Data:", ohlc_data)

                time.sleep(2)  # Wait for 2 seconds before the next iteration

            # Set open price to the first tick's price
            ohlc_data['open'] = ohlc_data['close']

            # Write to CSV
            write_to_csv('EURUSD_Candlestick_14s_ASK_30.09.2019-30.09.2022.csv', ohlc_data)

    except KeyboardInterrupt:
        print("Program stopped.")


