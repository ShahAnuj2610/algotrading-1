import logging

from trading.indicators.AverageTrueRange import AverageTrueRange
from trading.indicators.SuperTrend import SuperTrend
from trading.indicators.SuperTrendBand import SuperTrendBand
from trading.indicators.TrueRange import TrueRange
from trading.strategies.Strategy import Strategy
from trading.zerodha.kite.Period import Period


class SuperTrend73Strategy(Strategy):
    def __init__(self, kite, symbol, **kwargs):
        self.kite = kite

        # Initialise all strategy params
        self.candle_length = 7
        self.mode = kwargs['mode']
        self.candle_interval = kwargs['candle_interval']
        self.db_path = kwargs['db_path']
        self.period = Period.MIN
        self.multiplier = 3
        # This initialisation is necessary for the strategies to access the value
        # DO NOT remove this thinking it is redundant
        self.symbol = symbol

        # Initialise all indicators
        self.true_range_indicator = TrueRange(self, **kwargs)
        self.average_true_range_indicator = AverageTrueRange(self, **kwargs)

        self.super_trend_band_indicator = SuperTrendBand(self, multiplier=self.multiplier, **kwargs)

        self.super_trend_indicator = SuperTrend(self, **kwargs)
        # The order of the indicators matter
        # Ordered by dependencies
        super().__init__(kite,
                         symbol,
                         [
                             self.true_range_indicator,
                             self.average_true_range_indicator,
                             self.super_trend_band_indicator,
                             self.super_trend_indicator
                         ],
                         **kwargs)

    def act(self, candle_time):
        super_trend = self.super_trend_indicator.get_lines(2, candle_time)

        prev_color = super_trend['color'][0]
        new_color = super_trend['color'][1]

        new_super_trend_value = super_trend[self.super_trend_indicator.indicator_name][1]
        curr_price = super_trend['close'][1]

        if (prev_color == "na" and new_color == "red") or (prev_color == "green" and new_color == "red"):
            self.stop_and_reverse_enter_short_position(candle_time, curr_price)
        elif (prev_color == "na" and new_color == "green") or (prev_color == "red" and new_color == "green"):
            self.stop_and_reverse_enter_long_position(candle_time, curr_price)

    def get_true_range_indicator(self):
        return self.true_range_indicator

    def get_average_true_range_indicator(self):
        return self.average_true_range_indicator

    def get_super_trend_band_indicator(self):
        return self.super_trend_band_indicator

    def get_super_trend_indicator(self):
        return self.super_trend_indicator
