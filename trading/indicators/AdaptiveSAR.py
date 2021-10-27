from trading.indicators.Indicator import Indicator


class AdaptiveSAR(Indicator):
    def __init__(self, strategy, **kwargs):
        self.average_true_range = strategy.get_average_true_range_indicator()
        self.atr_name = self.average_true_range.__class__.__name__
        self.arc = 3

        super().__init__(self.__class__.__name__, strategy, **kwargs)

    def do_calculate_lines(self, candle_time):
        sar_df = self.get_previous_indicator_value(candle_time)

        if sar_df.empty:
            atr_df = self.average_true_range.get_lines(2, candle_time)
            self.calculate_sar(atr_df, candle_time)
            return

        atr_df = self.average_true_range.get_lines(1, candle_time)

        df = sar_df.append(atr_df)
        ticks_df = self.get_data(candle_time)

        self.validate_candles_and_throw(df, reversed(self.get_n_candle_sequence(2, candle_time)))

        if df['color'][0] == "green":
            self.calculate_sar_from_long_trade(df, ticks_df, candle_time)
        else:
            self.calculate_sar_from_short_trade(df, ticks_df, candle_time)

    def calculate_sar_from_short_trade(self, df_in, ticks_df, candle_time):
        df = df_in.copy()

        ind = df.index
        for i in range(1, len(df)):
            # Before making further calculations, check if the high has breached SAR that was calculated previously
            # The SAR value that was obtained by tailing self.df.values is the SAR that was already calculated for
            # this candle

            # If current close greater than SAR set for today, then we are going long
            if df['close'][i] > df[self.indicator_name][i - 1]:
                df.loc[ind[i], 'SIC'] = df['close'][i]
                df.loc[ind[i], self.indicator_name] = df['SIC'][i] - (df[self.atr_name][i] * self.arc)
                df.loc[ind[i], 'color'] = "green"
                break

            df.loc[ind[i], 'SIC'] = min(ticks_df['close'])

            df.loc[ind[i], 'color'] = df['color'][i - 1]
            df.loc[ind[i], self.indicator_name] = df['SIC'][i] + (df[self.atr_name][i] * self.arc)

        self.store_indicator_value(df.tail(1), candle_time)

    def calculate_sar_from_long_trade(self, df_in, ticks_df, candle_time):
        df = df_in.copy()

        ind = df.index
        for i in range(1, len(df)):
            # Before making further calculations, check if the low has breached SAR that was calculated previously
            # The SAR value that was obtained by tailing self.df.values is the SAR that was already calculated for
            # this candle

            # If current low less than SAR set for today, then we are going short
            if df['close'][i] < df[self.indicator_name][i - 1]:
                df.loc[ind[i], 'SIC'] = df['close'][i]
                df.loc[ind[i], self.indicator_name] = df['SIC'][i] + (df[self.atr_name][i] * self.arc)
                df.loc[ind[i], 'color'] = "red"
                break

            df.loc[ind[i], 'SIC'] = max(ticks_df['close'])

            df.loc[ind[i], 'color'] = df['color'][i - 1]
            df.loc[ind[i], self.indicator_name] = df['SIC'][i] - (df[self.atr_name][i] * self.arc)

        self.store_indicator_value(df.tail(1), candle_time)

    def calculate_sar(self, atr_df_in, candle_time):
        df = self.calculate_base_params(atr_df_in)
        self.store_indicator_value(df.tail(1), candle_time)

    def calculate_base_params(self, atr_df_in):
        df = atr_df_in.copy()

        # The starting value is a guess
        if df['close'][0] < df['close'][1]:
            # We are in uptrend
            df['SIC'] = df['close']
            df[self.indicator_name] = df['SIC'] - (df[self.atr_name] * self.arc)
            df['color'] = "green"
        else:
            # We are in down trend
            df['SIC'] = df['close']
            df[self.indicator_name] = df['SIC'] + (df[self.atr_name] * self.arc)
            df['color'] = "red"

        return df
