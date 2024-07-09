# Code for the MACD strategy class used for live trading and backtesting

# Ref: https://www.investopedia.com/articles/forex/05/macddiverge.asp

import numpy as np
import pandas as pd

class Strategy:

    # Initialize data
    def init_data(self):
        self.data = pd.read_csv('historical_data.csv')

    # Set data for the strategy
    def set_data(self, data):
        self.data = data

    # Append new data (live) to the strategy
    def add_data(self, data):
        self.data = pd.concat([self.data, data], axis=0)

    # Calculate the MACD and the Signal lines
    def calculate_macd(self, prices, short_window=12, long_window=26, signal_window=9):
        short_ema = prices.ewm(span=short_window, adjust=False).mean()
        long_ema = prices.ewm(span=long_window, adjust=False).mean()

        # Calculate MACD and Signal lines
        macd_line = short_ema - long_ema
        signal_line = macd_line.ewm(span=signal_window, adjust=False).mean()
        macd_histogram = macd_line - signal_line

        df = pd.DataFrame()
        df['MACD Line'] = macd_line
        df['Signal Line'] = signal_line
        df['MACD Histogram'] = macd_histogram
        return df

    # Generate signals to trade
    def get_trades(self):
        bars = self.data.sort_index().reset_index().set_index(['symbol', 'timestamp'])
        lines = bars.groupby(['symbol'], as_index=False).apply(lambda data_values: self.calculate_macd(data_values.close))
        bars = pd.concat([bars, lines], axis=1)

        bars['signal'] = 0

        # Buy
        bars.loc[(bars.groupby('symbol')['MACD Line'].shift(1) > bars.groupby('symbol')['Signal Line'].shift(1)) & (bars.groupby('symbol')['MACD Line'].shift(2) < bars.groupby('symbol')['Signal Line'].shift(2)), 'signal'] = 1

        # Sell
        bars.loc[(bars.groupby('symbol')['MACD Line'].shift(1) < bars.groupby('symbol')['Signal Line'].shift(1)) & (bars.groupby('symbol')['MACD Line'].shift(2) > bars.groupby('symbol')['Signal Line'].shift(2)), 'signal'] = -1

        # Compute signal count
        bars['position'] = bars.groupby('symbol')['signal'].ffill()
        bars['position'].fillna(0, inplace=True)
        bars['abs_sig'] = bars['signal'].abs()
        bars['count'] = bars.groupby('symbol')['abs_sig'].cumsum()
        bars['count'] = bars.groupby('symbol')['count'].ffill()

        # Compute positions
        bars['abs_pos'] = bars['position'].abs()
        bars['signal_cum'] = bars.groupby(['symbol', 'count'])['abs_pos'].cumsum()

        # Compute signals
        bars['new_signal'] = 0
        bars['new_signal'] = bars['position'] - bars.groupby('symbol')['position'].shift(1)
        bars.reset_index(level='symbol', inplace=True)

        final_trades = bars.groupby('symbol')['new_signal'].last()
        return bars, final_trades
