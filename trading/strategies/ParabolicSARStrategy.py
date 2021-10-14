import logging

from trading.indicators.ParabolicSAR import ParabolicSAR
from trading.strategies.Strategy import Strategy
from trading.zerodha.kite.Period import Period


class ParabolicSARStrategy(Strategy):
    def __init__(self, kite, symbol, **kwargs):
        # Initialise all strategy params
        self.candle_length = 2
        self.candle_interval = 1
        self.period = Period.MIN

        # This initialisation is necessary for the strategies to access the value
        # DO NOT remove this thinking it is redundant
        self.symbol = symbol

        # Initialise all indicators
        self.parabolic_sar_indicator = ParabolicSAR(self, **kwargs)

        # The order of the indicators matter
        # Ordered by dependencies
        super().__init__(kite,
                         symbol,
                         [
                             self.parabolic_sar_indicator
                         ],
                         **kwargs)

    def act(self, candle_time):
        parabolic_sar = self.parabolic_sar_indicator.get_lines(2, candle_time)

        prev_color = parabolic_sar['color'][0]
        new_color = parabolic_sar['color'][1]

        new_sar_value = parabolic_sar[self.parabolic_sar_indicator.indicator_name][1]
        curr_price = parabolic_sar['close'][1]

        if (prev_color == "na" and new_color == "red") or (prev_color == "green" and new_color == "red"):
            logging.info("Entering short position at {}".format(candle_time))
            # self.enter_short_position(candle_time, curr_price, new_sar_value)
        elif (prev_color == "na" and new_color == "green") or (prev_color == "red" and new_color == "green"):
            logging.info("Entering long position at {}".format(candle_time))
            # self.enter_long_position(candle_time, curr_price, new_sar_value)

    def get_parabolic_sar_indicator(self):
        return self.parabolic_sar_indicator
