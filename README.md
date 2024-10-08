﻿# TelegramTradingBot

﻿# Trading Bot with Emergency Stop
This Python-based trading bot is designed to monitor real-time OHLC (Open-High-Low-Close) data from the BirdEye API and execute buy/sell signals based on various technical indicators like RSI (Relative Strength Index) and moving averages (MA). Additionally, it includes an emergency stop feature to halt the trading process if low price activity is detected, i.e., when two consecutive OHLC values are identical.

﻿# Key Features
OHLC Data Collection: The bot collects OHLC data for the provided address and fetches real-time prices via BirdEye's API.
Technical Analysis: Uses TA-Lib for calculating technical indicators like RSI and moving averages (Exponential Moving Average and Simple Moving Average).
Buy/Sell Signals:
Buy signals are generated when short-term price trends (short MA) cross above long-term trends (long MA) and certain RSI thresholds are met.
Sell signals are triggered when short-term trends decline below long-term trends or when RSI drops below a certain value.
Emergency Stop: If the OHLC data remains the same over two periods (indicating stagnant prices), the bot stops and sends notifications to predefined Telegram channels.
Volume Analysis: Integrates volume data into the decision-making process by retrieving M5 volume via the DexScreener API.
Telegram Notifications: The bot sends notifications for both buy/sell actions and emergency stops to two separate Telegram channels via the Telegram Bot API.

﻿# Components
OHLC Data Formatting: Converts the fetched price into OHLC format with an additional volume field.
CSV Management: Records OHLC data in CSV format for further analysis.
Buy/Sell Signal Generation: Generates signals based on customized technical analysis rules (MA crossovers, RSI conditions).
Emergency Stop Feature: Stops trading when price activity is too low, preventing unnecessary trades in stagnant markets.
Telegram Integration: Sends real-time updates to Telegram channels, ensuring timely notifications for trading decisions and emergency stops.
