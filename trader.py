# Code to place live trades based on the MACD strategy

# Taken inspiration from the following reference:
# https://github.com/alpacahq/alpaca-trade-api-python/blob/master/examples/websockets/streamconn_on_and_off.py

import math
import time
import pandas as pd
import requests
import warnings
import datetime
import pytz
from concurrent.futures import ThreadPoolExecutor

from alpaca_trade_api.common import URL
from alpaca_trade_api.stream import Stream
from alpaca_trade_api.rest import TimeFrame, TimeFrameUnit
import alpaca_trade_api as trade_api

from strategy import Strategy

warnings.filterwarnings("ignore")

# Global constants
API_KEY = "PKKOW6NA36YDO9V198T6"
SECRET_KEY = "hx2Qpb1AvTpst3V7dmKMPVBefVqUQ24cngbU3tnb"
BASE_URL = 'https://paper-api.alpaca.markets'
ORDERS_URL = '{}/v2/orders'.format(BASE_URL)
SYMBOLS = ['AAPL', 'TSLA', 'MSFT', 'NFLX', 'AMZN', 'GOOGL', 'PYPL', 'META']
DATA_COLUMNS = ['symbol', 'open', 'close', 'low', 'high']

# Global variables
symbol_agg_time = {key: 0 for key in SYMBOLS}
data_agg_dict_symbols = {key: pd.DataFrame(columns=DATA_COLUMNS, index=['timestamp']) for key in SYMBOLS}
trading_window_agg = 6

rest = trade_api.REST(key_id=API_KEY, secret_key=SECRET_KEY, base_url='https://paper-api.alpaca.markets')
conn = Stream(API_KEY, SECRET_KEY, base_url=URL('https://paper-api.alpaca.markets'), data_feed='iex')

# Helper function to aggregate live data acquired within the time window
def aggregate_data(df, symbol):
    # Aggregate over all columns

    # Open: open value of the first row of the window
    # Close: close value of the last row of the window
    # Low: min low value of the window
    # High: max high value of the window
    agg_data = {
        'symbol': symbol,
        'open': df.iloc[0]['open'],
        'close': df.iloc[-1]['close'],
        'high': df['high'].max(),
        'low': df['low'].min()
    }

    # Update the index and timestamps
    agg_data = pd.DataFrame.from_dict([agg_data])
    agg_data.index = [datetime.datetime.now(tz=pytz.timezone('GMT')).replace(second=0, microsecond=0)]
    agg_data.index.name = 'timestamp'
    return agg_data

# Helper function to place an order
def place_order(symbol, quantity, side):
    data = {
            'symbol': symbol,
            'qty': quantity,
            'side': side,
            'type': 'market',
            'time_in_force': 'day'
    }
    headers = {
        'APCA-API-KEY-ID': API_KEY,
        'APCA-API-SECRET-KEY': SECRET_KEY
    }

    # Make a POST call to place the order
    r = requests.post(ORDERS_URL, headers=headers, json=data)

    # Write the placed order to a file
    with open(file='orders.txt', mode='a') as file:
        file.write(r.content.decode('utf-8'))
        file.write('\n')

# Handler function which gets called whenever we receive a data stream
async def bar_handler(bar):
    global symbol_agg_time

    bar_df = pd.DataFrame.from_dict([{'timestamp': pd.to_datetime(bar.timestamp, utc=True), 'open': bar.open, 'close': bar.close,
                'high': bar.high, 'low': bar.low, 'symbol': bar.symbol}])
    bar_df.set_index('timestamp', inplace=True)

    symbol = bar.symbol

    # Add the newly acquired bar to data_agg_dict_symbols which will be used to aggregate within the given window
    if symbol_agg_time[symbol] == 0:
        data_agg_dict_symbols[symbol] = bar_df
    else:
        data_agg_dict_symbols[symbol] = pd.concat([data_agg_dict_symbols[symbol], bar_df])

    # Increment symbol_agg_time[symbol] whenever we receive a data stream
    # Used to determine whether the data has been aggregated
    symbol_agg_time[symbol] += 1

    # If we reach the end of the time window, aggregate data and generate signals
    if datetime.datetime.now().minute % trading_window_agg == 0:

        # Add aggregated data to strategy
        s.add_data(aggregate_data(data_agg_dict_symbols[symbol], symbol))

        # Trade based on the newly added data
        _, signal = s.get_trades()
        symbol_agg_time[symbol] = 0
        capital_to_invest = float(rest.get_account().cash) / len(SYMBOLS)

        # If we have cash to invest, compute the quantity and place the order
        if capital_to_invest > 0:
            qty = math.floor(capital_to_invest / bar_df['close'])
            if signal[symbol] > 0:
                place_order(symbol, qty, 'buy')
            elif signal[symbol] < 0:
                place_order(symbol, qty, 'sell')


# Thread to subscribe to live data stream
def consumer_thread():
    global conn

    # Subscribe to each symbol and add a handler instance for each
    for i in range(len(SYMBOLS)):
        conn.subscribe_bars(bar_handler, SYMBOLS[i])

    conn.run()

if __name__ == '__main__':
    pool = ThreadPoolExecutor(1)

    # Get historical data
    historical_data = rest.get_bars(symbol=SYMBOLS, timeframe=TimeFrame(trading_window_agg, TimeFrameUnit.Minute), start='2021-01-01').df
    historical_data = historical_data[DATA_COLUMNS]
    historical_data.to_csv('historical_data.csv')

    s = Strategy()
    s.init_data()

    # Resetting connection every 600 seconds
    while 1:
        try:
            pool.submit(consumer_thread)
            time.sleep(600)
            conn.stop()
            time.sleep(5)
        except KeyboardInterrupt:
            print("Interrupted execution by user")
            conn.stop()
            exit(0)
        except Exception as e:
            # Let the execution continue and don't return
            print(f"You got an exception: {e} during execution. continue "
                  "execution.")
