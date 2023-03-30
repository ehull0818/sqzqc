#region imports
from AlgorithmImports import *
#endregion
## Algo input parameters

# Risk parameters
start_date = (2015, 1, 1)
end_date = (2023, 1, 1)
starting_account_balance = 25_000
per_trade_notional = 5_000



# Fixed ticker list
stock_ticker_list = 'QQQ', 'SPY', 'IWM', 'HYG', 'EEM'  #'AMZN', 'GOOGL', 'FB', 'AAPL', 'NFLX', 'NVDA', 'MSFT'

# Stock universe parameters, sorted by daily dollar volume
use_stock_universe = False  # Set to False for Fixed ticker list
stock_universe_size = 200
minimum_price = 50



## Exit parameters
# ATR Trailing Stop
use_atr_trailing_stop = True            # True or False
use_daily_atr_for_trailing_stop = True  # True -> daily, False -> intraday
atr_trailing_stop_period = 21           # Lookback period for ATR calc
atr_trailing_stop_multiplier = 2

# Percent of stock price trailing stop
use_percent_trailing_stop = True    # Trur or False
percent_trailing_stop = 2.00       # 5.00% notated as 5.00

# Time based trade exit
use_time_stop = False                # True of False
time_stop_hold_days = 999



## Profit target parameters
# ATR profit traget based on distance from ema_med_period
use_atr_profit_target = True            # True or False
use_daily_atr_for_profit_target = True  # True -> daily, False -> intraday
atr_profit_target_period = 21           # Lookback period for ATR calc
atr_profit_target_multiplier = 2



# Timeframe parameters
timeframe_intraday = 30 # Number of minutes

# Indicator parameters
use_squeeze_intraday = False
min_bars_squeeze_intraday = 2

use_squeeze_daily = True
min_bars_squeeze_daily = 2

use_squeeze_weekly = False
min_bars_squeeze_weekly = 1

ema_fast_period = 8
ema_med_period = 21
ema_slow_period = 34

squeeze_period = 20
bollinger_stdev = 2
keltner_atr = 1.5

# Option parameters
use_options = True
premium_offset_multiplier = 1.5
minimum_days_expiration = 45
minimum_delta = 0.7
