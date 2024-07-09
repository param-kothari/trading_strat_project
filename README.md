# Trading Project

## Objective

Simulate a trading strategy and execute it to place live orders on Alpaca. The project includes utilities for creating a trading strategy, backtesting against historical data, and placing real-time orders using the Alpaca API.

## Files Used

### `schedule_trades.py`

- Schedules and runs the trading file during trading hours.
- Uses the “schedule” module to start at 8:30 AM (Chicago Time) and run until 3:00 PM (Chicago Time).

### `strategy.py`

- Implements a trading strategy using the MACD strategy.
- Generates MACD and Signal lines to produce buy (+1) or sell (-1) signals.
- The strategy class reads historical CSV data and incorporates live aggregated data in a concatenated dataframe.

### `backtest.py`

- Backtests the trading strategy on historical data obtained via the Alpaca API.
- Simulates trading based on generated signals to assess strategy performance and fine-tune parameters.

### `trader.py`

- Places live trades based on a live data stream.
- Utilizes a consumer thread to subscribe to data streams and aggregate live data.
- Generates signals and places orders at specific intervals, recording the orders in a text file.

## Results

- Backtested the MACD trading strategy on this year's historical data for the same symbols used in live trading.
- Achieved returns of 0.22 and a Sharpe ratio of 1.422 with 15-minute aggregates.
- Ran the live trading on December 8 with symbols: 'AAPL', 'TSLA', 'MSFT', 'NFLX', 'AMZN', 'GOOGL', 'PYPL', 'META'.
- Ended with a final portfolio value of 99137.83 USD.
