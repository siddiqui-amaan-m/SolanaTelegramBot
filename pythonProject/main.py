import requests
import json
import time
import talib
import numpy as np
from datetime import datetime

def fetch_current_price(retry_delay=1.5):
    url = "https://public-api.birdeye.so/public/price?address=2LmT5vqopEVneRBKSdi9LFPJQKLZ72U5VKHc93CJmw3f"
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
            time.sleep(retry_delay)

def generate_fast_scalping_signal(current_price, price_change_threshold=0.005):
    historical_data = []

    # Fetch historical data including high, low, and close prices
    for _ in range(3):  # Adjust the window size for faster scalping
        time.sleep(1)  # Wait for 1 second for a faster strategy
        historical_data.append(fetch_current_price())
        print(fetch_current_price())

    historical_data = np.array(historical_data, dtype=np.float64)


    # Check if the data has more than one element
    if historical_data.size > 1:
        close_prices = historical_data
        print(close_prices)
        # Calculate Rate of Change (ROC)
        roc = talib.ROC(close_prices, timeperiod=2)


        # Check if there are NaN values in the ROC array
        if np.isnan(roc).any():
            roc[np.isnan(roc)] = 0
            print(roc)

        # Calculate Stochastic Oscillator
        _, stochastic_oscillator = talib.STOCH(close_prices, close_prices, close_prices, fastk_period=3, slowk_period=3, slowd_period=3)
        print(stochastic_oscillator)
        # Check if there are NaN values in the Stochastic Oscillator array
        if np.isnan(stochastic_oscillator).any():
            return "Hold"

        # Calculate the price change percentage
        price_change_percentage = (current_price - historical_data[-2]) / historical_data[-2]
        print(price_change_percentage)
        # Strategy: Buy when ROC is positive, Stochastic Oscillator is low, and price change is significant
        # Sell when ROC is negative, Stochastic Oscillator is high, and price change is significant
        if roc[-1] > 0 and stochastic_oscillator[-1] < 20 and price_change_percentage > price_change_threshold:
            return "Buy"
        elif roc[-1] < 0 and stochastic_oscillator[-1] > 80 and price_change_percentage < -price_change_threshold:
            return "Sell"
        else:
            return "Hold"
    else:
        return "Hold"

if __name__ == "__main__":
    try:

        while True:
            current_price = fetch_current_price()
            if current_price is not None:
                signal = generate_fast_scalping_signal(current_price=current_price)
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"{current_time} - Current Price: {current_price}, Signal: {signal}")
            # time.sleep(1)  # Wait for 1 second before the next iteration

    except KeyboardInterrupt:
        print("Trading bot stopped.")
