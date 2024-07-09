# Code to backtest implemented strategy

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from alpaca_trade_api.rest import TimeFrame, TimeFrameUnit
import alpaca_trade_api as trade_api

from strategy import Strategy

API_KEY = "PKKOW6NA36YDO9V198T6"
SECRET_KEY = "hx2Qpb1AvTpst3V7dmKMPVBefVqUQ24cngbU3tnb"
BASE_URL = 'https://paper-api.alpaca.markets'

# Function to calculate various performance metrics
def calculate_metrics(returns_df, returns, trading_bars_per_year=252):
    returns_df['timestamp'] = returns_df.index
    cum_returns = returns_df['Cum Returns']

    # Calculate Total Returns
    total_returns = cum_returns.iloc[-1] - 1

    # Calculate Annualized Returns
    days = len(returns_df)
    annualized_returns = (total_returns + 1) ** (trading_bars_per_year / days) - 1

    # Calculate Annualized Volatility
    annualized_volatility = returns.std() * np.sqrt(trading_bars_per_year)

    # Calculate Sharpe Ratio
    sharpe_ratio = annualized_returns / annualized_volatility

    # Calculate Success Rate
    positive_returns = returns[returns > 0]
    success_rate = len(positive_returns) / len(returns)

    metrics = {
        'Returns': annualized_returns,
        'Volatility': annualized_volatility,
        'Sharpe Ratio': sharpe_ratio,
        'Success Rate': success_rate
    }
    plot(cumulative_returns=returns_df, total_returns=returns, metrics=metrics)


def plot(cumulative_returns, total_returns, metrics):
    # Plotting Cumulative Returns Over Time
    plt.figure(figsize=(12, 10))
    sns.set(style="whitegrid")
    sns.lineplot(data=cumulative_returns, x=cumulative_returns.index, y='Returns', color='red')
    plt.title('Returns Vs Time')
    plt.xlabel('Timestamp')
    plt.ylabel('Returns')
    plt.xticks(rotation=45)

    # Print and display additional metrics
    print("Additional Metrics:")
    for key, value in metrics.items():
        print(f"{key}: {value:.6f}")
    plt.show()


class BacktesterClass:
    def __init__(self, data):
        self.data = data

    def add_data(self, data):
        self.data = data.drop_duplicates()

    def returns(self):
        self.data['typical_price'] = (self.data['close'] + self.data['low'] + self.data['high']) / 3
        returns_df = self.data.pivot(columns=['symbol'], values=['typical_price'])
        returns_df = returns_df.pct_change()
        positions_df = self.data.pivot(columns=['symbol'], values=['position'])
        positions_df = positions_df[2:].replace(np.nan, 0)
        returns_df = returns_df[2:].replace(np.nan, 0)
        positions_df.columns = sorted(self.data['symbol'].unique())
        returns_df.columns = sorted(self.data['symbol'].unique())
        daily_returns = positions_df.shift() * returns_df
        daily_portfolio_returns = daily_returns.mean(axis=1)
        cumulative_portfolio_returns = (1 + daily_portfolio_returns).cumprod()
        cumulative_returns_df = pd.DataFrame(cumulative_portfolio_returns, columns=['Returns'])
        return cumulative_returns_df, daily_portfolio_returns

if __name__ == '__main__':
    rest = trade_api.REST(key_id=API_KEY, secret_key=SECRET_KEY,
                              base_url='https://paper-api.alpaca.markets')
    data = rest.get_bars(symbol=['AAPL', 'TSLA', 'MSFT', 'NFLX', 'AMZN', 'GOOGL', 'PYPL', 'META'], timeframe=TimeFrame(15, TimeFrameUnit.Minute), start='2021-01-01').df
    s = Strategy()
    s.add_new_data(data)
    trade_data, last_signals = s.get_trades()

    b = BacktesterClass(trade_data)
    cum_returns, returns = b.returns()
    cum_returns.columns = ['Cumulative Returns']
    calculate_metrics(cum_returns, returns, 16128)
