from trading.indicators.AverageTrueRange import AverageTrueRange
from trading.indicators.AdaptiveSAR import AdaptiveSAR
from trading.indicators.TrueRange import TrueRange
from trading.strategies.Strategy import Strategy
from trading.zerodha.kite.Period import Period


class AdaptiveSARStrategy(Strategy):
    def __init__(self, kite, symbol, **kwargs):
        # Initialise all strategy params
        self.kite = kite
        self.candle_length = 7
        self.mode = kwargs['mode']
        self.candle_interval = kwargs['candle_interval']
        self.db_path = kwargs['db_path']
        self.period = Period.MIN

        # This initialisation is necessary for the strategies to access the value
        # DO NOT remove this thinking it is redundant
        self.symbol = symbol

        # Initialise all indicators
        self.true_range_indicator = TrueRange(self, **kwargs)
        self.average_true_range_indicator = AverageTrueRange(self, **kwargs)
        self.adaptive_sar_indicator = AdaptiveSAR(self, **kwargs)

        # The order of the indicators matter
        # Ordered by dependencies
        super().__init__(kite,
                         symbol,
                         [
                             self.true_range_indicator,
                             self.average_true_range_indicator,
                             self.adaptive_sar_indicator
                         ],
                         **kwargs)

    def act(self, candle_time):
        sar = self.adaptive_sar_indicator.get_lines(2, candle_time)

        prev_color = sar['color'][0]
        new_color = sar['color'][1]

        curr_price = sar['close'][1]

        if (prev_color == "na" and new_color == "red") or (prev_color == "green" and new_color == "red"):
            self.enter_short_position(candle_time, curr_price, 0)
        elif (prev_color == "na" and new_color == "green") or (prev_color == "red" and new_color == "green"):
            self.enter_long_position(candle_time, curr_price, 0)

    def get_true_range_indicator(self):
        return self.true_range_indicator

    def get_average_true_range_indicator(self):
        return self.average_true_range_indicator


