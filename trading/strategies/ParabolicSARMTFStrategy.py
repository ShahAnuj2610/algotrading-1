from trading.indicators.ParabolicSAR import ParabolicSAR
from trading.strategies.Strategy import Strategy
from trading.zerodha.kite.Period import Period


class ParabolicSARMTFStrategy(Strategy):
    def __init__(self, kite, symbol, **kwargs):
        # Initialise all strategy params
        self.kite = kite
        self.candle_length = 2
        self.mode = kwargs['mode']
        self.candle_interval_lt = kwargs['candle_interval_lt']
        self.candle_interval_ht = kwargs['candle_interval_ht']
        self.db_path = kwargs['db_path']
        self.period = Period.MIN

        # This initialisation is necessary for the strategies to access the value
        # DO NOT remove this thinking it is redundant
        self.symbol = symbol

        # Initialise all indicators
        self.parabolic_sar_indicator_lt = ParabolicSAR(self, candle_interval=self.candle_interval_lt, **kwargs)
        self.parabolic_sar_indicator_ht = ParabolicSAR(self, candle_interval=self.candle_interval_ht, **kwargs)

        # The order of the indicators matter
        # Ordered by dependencies
        super().__init__(kite,
                         symbol,
                         [
                             self.parabolic_sar_indicator_ht,
                             self.parabolic_sar_indicator_lt
                         ],
                         **kwargs)

    def act(self, candle_time):
        parabolic_sar_lt = self.parabolic_sar_indicator_lt.get_lines(2, candle_time)
        parabolic_sar_ht = self.parabolic_sar_indicator_ht.get_lines_unsafe(2)

        curr_price = parabolic_sar_lt['close'][1]

        # For now ignoring stop loss because parabolic SAW already trails the price
        stop_loss = 0

        # Major trend takes precedence
        # Typically minor trend would have reacted before the major trend
        if self.trend_changed_to_red(parabolic_sar_ht):
            if len(self.short_positions) == 1:
                # We are already in the right direction
                return

            self.stop_and_reverse_enter_short_position(candle_time, curr_price)
            return
        elif self.trend_changed_to_green(parabolic_sar_ht):
            if len(self.long_positions) == 1:
                # We are already in the right direction
                return

            self.stop_and_reverse_enter_long_position(candle_time, curr_price)
            return

        major_trend_color = self.get_major_trend_color(parabolic_sar_ht)

        if major_trend_color == "na":
            # We are in the first few data points where major trend has not been established yet
            return

        # Major trend has not shown any movement
        # We will now look at the minor trend
        # We use minor trend only to take early positions. Otherwise major trend has the say
        # The effect will be felt more in higher time frames like 3-15, 5-30 etc
        if self.trend_changed_to_red(parabolic_sar_lt)\
                and major_trend_color == "red" and len(self.short_positions) == 0:
            self.stop_and_reverse_enter_short_position(candle_time, curr_price)
        elif self.trend_changed_to_green(parabolic_sar_lt) and major_trend_color == "green" and len(self.long_positions) == 0:
            self.stop_and_reverse_enter_long_position(candle_time, curr_price)

    def trend_changed_to_red(self, df):
        if len(df) != 2:
            return False

        prev_color = df['color'][0]
        new_color = df['color'][1]

        if prev_color == "green" and new_color == "red":
            return True

        return False

    def trend_changed_to_green(self, df):
        if len(df) != 2:
            return False

        prev_color = df['color'][0]
        new_color = df['color'][1]

        if prev_color == "red" and new_color == "green":
            return True

        return False

    def get_major_trend_color(self, df):
        if df.empty:
            return "na"
        if len(df) == 1:
            return df['color'][0]
        elif len(df) == 2:
            return df['color'][1]
        else:
            return ValueError("Unable to determine major trend color")


