from trading.indicators.Indicator import Indicator


class DX(Indicator):
    def __init__(self, strategy, **kwargs):
        self.true_range = strategy.get_true_range_indicator()

        super().__init__(self.__class__.__name__, strategy, **kwargs)

    def do_calculate_lines(self, candle_time):
        adx_df = self.get_previous_indicator_value(candle_time)

        if adx_df.empty:
            self.calculate_dx(candle_time)
            return

        tr_df = self.true_range.get_lines(1, candle_time)

        df = adx_df.append(tr_df)
        self.validate_candles_and_throw(df, reversed(self.get_n_candle_sequence(2, candle_time)))

        df = self.calculate_base_params(df)

        ind = df.index
        for i in range(1, len(df)):
            df.loc[ind[i], 'TR_14'] = (df['TR_14'][i - 1] - (df['TR_14'][i - 1] / self.candle_length)) + df['TR_14'][i]
            df.loc[ind[i], 'PLUSDM_14'] = (df['PLUSDM_14'][i - 1] - (df['PLUSDM_14'][i - 1] / self.candle_length)) + \
                                      df['PLUSDM_1'][i]
            df.loc[ind[i], 'MINUSDM_14'] = (df['MINUSDM_14'][i - 1] - (df['MINUSDM_14'][i - 1] / self.candle_length)) + \
                                       df['MINUSDM_1'][i]
            df.loc[ind[i], 'PLUSDI_14'] = round((df['PLUSDM_14'][i] / df['TR_14'][i]) * 100)
            df.loc[ind[i], 'MINUSDI_14'] = round((df['MINUSDM_14'][i] / df['TR_14'][i]) * 100)
            df.loc[ind[i], 'DI_DIFF'] = abs(df['PLUSDI_14'][i] - df['MINUSDI_14'][i])
            df.loc[ind[i], 'DI_SUM'] = df['PLUSDI_14'][i] + df['MINUSDI_14'][i]

            if df['DI_SUM'][i] == 0:
                df.loc[ind[i], self.indicator_name] = 0
            else:
                df.loc[ind[i], self.indicator_name] = round((df['DI_DIFF'][i] / df['DI_SUM'][i]) * 100)

        self.store_indicator_value(df.tail(1), candle_time)

    def calculate_dx(self, candle_time):
        tr_df = self.true_range.get_lines(self.candle_length, candle_time)
        tr_df[['PLUSDM_1', 'MINUSDM_1', 'TR_14', 'PLUSDM_14', 'MINUSDM_14', 'PLUSDI_14', 'MINUSDI_14', 'DI_DIFF',
               'DI_SUM', self.indicator_name]] = 0

        df = self.calculate_base_params(tr_df)

        self.store_indicator_value(df.tail(1), candle_time)

    def calculate_base_params(self, df_in):
        df = df_in.copy()

        ind = df.index
        tr_sum = 0
        plus_dm_sum = 0
        minus_dm_sum = 0

        for i in range(1, len(df)):
            high_today = df['high'][i]
            high_yest = df['high'][i - 1]

            low_today = df['low'][i]
            low_yest = df['low'][i - 1]

            high_diff = high_today - high_yest
            low_diff = low_yest - low_today

            if high_diff > 0 and high_diff > low_diff:
                df.loc[ind[i], 'PLUSDM_1'] = high_diff
                df.loc[ind[i], 'MINUSDM_1'] = 0
                plus_dm_sum = plus_dm_sum + high_diff
            elif low_diff > 0 and low_diff > high_diff:
                df.loc[ind[i], 'MINUSDM_1'] = low_diff
                df.loc[ind[i], 'PLUSDM_1'] = 0
                minus_dm_sum = minus_dm_sum + low_diff
            else:
                df.loc[ind[i], 'MINUSDM_1'] = 0
                df.loc[ind[i], 'PLUSDM_1'] = 0

            tr_sum = tr_sum + df[self.true_range.indicator_name][i]

        ind = df.index
        i = len(df) - 1

        df.loc[ind[i], 'TR_14'] = tr_sum
        df.loc[ind[i], 'PLUSDM_14'] = plus_dm_sum
        df.loc[ind[i], 'MINUSDM_14'] = minus_dm_sum

        return df
