#region imports
from AlgorithmImports import *
#endregion
import datetime as dt
from QuantConnect.Securities.Option import OptionPriceModels
import config


class Strategy:
    '''Class to hold data and indicators for symbol
    '''
    def __init__(self, qc, equity_symbol) -> None:
        self.qc = qc
        self.equity_symbol = equity_symbol
        self.option_symbol = self.initialize_options()
        self.option_contract = None
        self.trade_time = None
        self.trailing_stop_ref_price = None
        self.trailing_stop_percent = None
        self.trailing_stop_atr = None
        self.target_atr = None
        self.initialize_consolidators()
        self.initialize_indicators()
        
        # Update consolidator with historial data
        self.bars_required = int((max(config.ema_slow_period, config.squeeze_period) + 1) * 6.5 * 60 * 5)    # 6.5 hrs/day, 60min/hr, 5days/week
        self.history = self.qc.History(self.equity_symbol, self.bars_required, Resolution.Minute).loc[self.equity_symbol]
        for bar in self.history.itertuples():
            tradebar = TradeBar(bar.Index, self.equity_symbol, bar.open, bar.high, bar.low, bar.close, bar.volume, timedelta(minutes=1))
            self.update(tradebar)


    def consolidator_intraday_custom(self, timestamp) -> CalendarInfo:
        '''Custom logic used to determine start time of intraday consolidator
        '''
        period = dt.timedelta(minutes=config.timeframe_intraday)
        start = timestamp.replace(minute=30)
        if start > timestamp:
            start -= period
            
        return CalendarInfo(start, period)


    def initialize_consolidators(self) -> None:
        '''Create consolidators and subscribe to market data
        '''
        # Create consolidator
        self.consolidator_intraday = TradeBarConsolidator(self.consolidator_intraday_custom)
        self.consolidator_daily = TradeBarConsolidator(dt.timedelta(days=1))
        self.consolidator_weekly = TradeBarConsolidator(Calendar.Weekly)
        
        # Attach event handler to consolidator
        self.consolidator_intraday.DataConsolidated += self.handler_intraday
        self.consolidator_daily.DataConsolidated += self.handler_daily
        self.consolidator_weekly.DataConsolidated += self.handler_weekly
        
        # Subscribe consolidator to data
        self.qc.SubscriptionManager.AddConsolidator(self.equity_symbol, self.consolidator_intraday)
        self.qc.SubscriptionManager.AddConsolidator(self.equity_symbol, self.consolidator_daily)
        self.qc.SubscriptionManager.AddConsolidator(self.equity_symbol, self.consolidator_weekly)


    def initialize_indicators(self) -> None:
        '''Create indicators and rolling windows to store data
        '''
        # Create indicator
        self._atr_intraday = AverageTrueRange(config.atr_trailing_stop_period, MovingAverageType.Simple)
        self._atr_daily = AverageTrueRange(config.atr_trailing_stop_period,  MovingAverageType.Simple)
        
        self._ema_fast_intraday = ExponentialMovingAverage(config.ema_fast_period)
        self._ema_fast_daily = ExponentialMovingAverage(config.ema_fast_period)
        self._ema_fast_weekly = ExponentialMovingAverage(config.ema_fast_period)
        
        self._ema_med_intraday = ExponentialMovingAverage(config.ema_med_period)
        self._ema_med_daily = ExponentialMovingAverage(config.ema_med_period)
        self._ema_med_weekly = ExponentialMovingAverage(config.ema_med_period)
        
        self._ema_slow_intraday = ExponentialMovingAverage(config.ema_slow_period)
        self._ema_slow_daily = ExponentialMovingAverage(config.ema_slow_period)
        self._ema_slow_weekly = ExponentialMovingAverage(config.ema_slow_period)
        
        self._bollinger_intraday = BollingerBands(config.squeeze_period, config.bollinger_stdev, MovingAverageType.Simple)
        self._bollinger_daily = BollingerBands(config.squeeze_period, config.bollinger_stdev, MovingAverageType.Simple)
        self._bollinger_weekly = BollingerBands(config.squeeze_period, config.bollinger_stdev, MovingAverageType.Simple)
        
        self._keltner_intraday = KeltnerChannels(config.squeeze_period, config.keltner_atr, MovingAverageType.Simple)
        self._keltner_daily = KeltnerChannels(config.squeeze_period, config.keltner_atr, MovingAverageType.Simple)
        self._keltner_weekly = KeltnerChannels(config.squeeze_period, config.keltner_atr, MovingAverageType.Simple)
        
        # Create rolling window
        self.price_intraday = RollingWindow[TradeBar](5)
        self.price_daily = RollingWindow[TradeBar](5)
        self.price_weekly = RollingWindow[TradeBar](5)
        
        self.atr_daily = RollingWindow[AverageTrueRange](5)
        self.atr_intraday = RollingWindow[AverageTrueRange](5)
        
        self.ema_fast_intraday = RollingWindow[ExponentialMovingAverage](5)
        self.ema_fast_daily = RollingWindow[ExponentialMovingAverage](5)
        self.ema_fast_weekly = RollingWindow[ExponentialMovingAverage](5)
        
        self.ema_med_intraday = RollingWindow[ExponentialMovingAverage](5)
        self.ema_med_daily = RollingWindow[ExponentialMovingAverage](5)
        self.ema_med_weekly = RollingWindow[ExponentialMovingAverage](5)
        
        self.ema_slow_intraday = RollingWindow[ExponentialMovingAverage](5)
        self.ema_slow_daily = RollingWindow[ExponentialMovingAverage](5)
        self.ema_slow_weekly = RollingWindow[ExponentialMovingAverage](5)
        
        self.bollinger_intraday = RollingWindow[BollingerBands](5)
        self.bollinger_daily = RollingWindow[BollingerBands](5)
        self.bollinger_weekly = RollingWindow[BollingerBands](5)
        
        self.keltner_intraday = RollingWindow[KeltnerChannels](5)
        self.keltner_daily = RollingWindow[KeltnerChannels](5)
        self.keltner_weekly = RollingWindow[KeltnerChannels](5)


    @property
    def is_ready(self) -> bool:
        return self._ema_slow_weekly.IsReady and self._bollinger_weekly.IsReady


    def update(self, bar) -> None:
        '''Update each consolidator with new data point
        '''
        self.consolidator_intraday.Update(bar)
        self.consolidator_daily.Update(bar)
        self.consolidator_weekly.Update(bar)


    def handler_intraday(self, sender, bar) -> None:
        '''Event hander for intraday timeframe
        '''
        # Update indicator
        self._atr_intraday.Update(bar)
        self._ema_fast_intraday.Update(bar.EndTime, bar.Close)
        self._ema_med_intraday.Update(bar.EndTime, bar.Close)
        self._ema_slow_intraday.Update(bar.EndTime, bar.Close)
        self._bollinger_intraday.Update(bar.EndTime, bar.Close)
        self._keltner_intraday.Update(bar)
        
        # Update rolling window
        self.price_intraday.Add(bar)
        self.atr_intraday.Add(self._atr_intraday)
        self.ema_fast_intraday.Add(self._ema_fast_intraday)
        self.ema_med_intraday.Add(self._ema_med_intraday)
        self.ema_slow_intraday.Add(self._ema_slow_intraday)
        self.bollinger_intraday.Add(self._bollinger_intraday)
        self.keltner_intraday.Add(self._keltner_intraday)


    def handler_daily(self, sender, bar) -> None:
        '''Event hander for daily timeframe
        '''
        # Update indicator
        self._atr_daily.Update(bar)
        self._ema_fast_daily.Update(bar.EndTime, bar.Close)
        self._ema_med_daily.Update(bar.EndTime, bar.Close)
        self._ema_slow_daily.Update(bar.EndTime, bar.Close)
        self._bollinger_daily.Update(bar.EndTime, bar.Close)
        self._keltner_daily.Update(bar)
        
        # Update rolling window
        self.price_daily.Add(bar)
        self.atr_daily.Add(self._atr_daily)
        self.ema_fast_daily.Add(self._ema_fast_daily)
        self.ema_med_daily.Add(self._ema_med_daily)
        self.ema_slow_daily.Add(self._ema_slow_daily)
        self.bollinger_daily.Add(self._bollinger_daily)
        self.keltner_daily.Add(self._keltner_daily)


    def handler_weekly(self, sender, bar) -> None:
        '''Event hander for weekly timeframe
        '''
        # Update indicator
        self._ema_fast_weekly.Update(bar.EndTime, bar.Close)
        self._ema_med_weekly.Update(bar.EndTime, bar.Close)
        self._ema_slow_weekly.Update(bar.EndTime, bar.Close)
        self._bollinger_weekly.Update(bar.EndTime, bar.Close)
        self._keltner_weekly.Update(bar)
        
        # Update rolling window
        self.price_weekly.Add(bar)
        self.ema_fast_weekly.Add(self._ema_fast_weekly)
        self.ema_med_weekly.Add(self._ema_med_weekly)
        self.ema_slow_weekly.Add(self._ema_slow_weekly)
        self.bollinger_weekly.Add(self._bollinger_weekly)
        self.keltner_weekly.Add(self._keltner_weekly)


    def initialize_options(self) -> Symbol:
        '''Request options data and set filters
        '''
        if not config.use_options: return None
        
        option = self.qc.AddOption(self.equity_symbol.Value, Resolution.Minute)
        option.SetFilter(lambda universe: universe.IncludeWeeklys().Strikes(-25,0).Expiration(TimeSpan.FromDays(config.minimum_days_expiration), TimeSpan.FromDays(config.minimum_days_expiration + 30)))
        
        return option.Symbol
