from trading.indicators.Indicator import Indicator


class TrueRange(Indicator):
    def __init__(self, strategy, **kwargs):
        super().__init__(self.__class__.__name__, strategy, **kwargs)

        # For true range, previous and current candles are enough
        self.candle_length = 2

    def do_calculate_lines(self, candle_time):
        tr_df = self.get_previous_indicator_value(candle_time)

        if tr_df.empty:
            ticks_df = self.get_data(candle_time)
            self.calculate_true_range(ticks_df, candle_time)
            return

        ticks_df = self.get_data_for_time(candle_time)
        df = tr_df.append(ticks_df)

        self.validate_candles_and_throw(df, reversed(self.get_n_candle_sequence(2, candle_time)))
        self.calculate_true_range(df, candle_time)

    def calculate_true_range(self, df_in, candle_time):
        df = df_in.copy()

        df['H-L'] = abs(df['high'] - df['low'])
        df['H-PC'] = abs(df['high'] - df['close'].shift(1))
        df['L-PC'] = abs(df['low'] - df['close'].shift(1))
        df[self.indicator_name] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1, skipna=False)

        df.dropna(inplace=True)
        df.drop('H-L', axis=1, inplace=True)
        df.drop('H-PC', axis=1, inplace=True)
        df.drop('L-PC', axis=1, inplace=True)

        self.store_indicator_value(df.tail(1), candle_time)

