from trading.indicators.Indicator import Indicator


class StructuralPivot(Indicator):
    def __init__(self, strategy, **kwargs):
        super().__init__(self.__class__.__name__, strategy, **kwargs)

        self.prev_small_pivot = "na"
        self.prev_small_pivot_idx = 0
        self.plt = None

    def do_calculate_lines(self, candle_time):
        ticks_df = self.get_data(candle_time)
        ticks_df['small_pivot_type'] = "na"
        ticks_df['bar1'] = "na"
        ticks_df['bar2'] = "na"
        self.store_indicator_value(ticks_df, candle_time)

        if len(self.values) - self.prev_small_pivot_idx < 3:
            # Enough candles to find a pivot has not formed yet
            return

        df = self.values.copy()

        if self.prev_small_pivot == "na":
            sp_df, sph_found, sph_index = self.calculate_small_pivot_high(df)

            if not sph_found:
                sp_df, spl_found, spl_index = self.calculate_small_pivot_low(df)
        elif self.prev_small_pivot == "sph":
            sp_df, sph_found, spl_index = self.calculate_small_pivot_low(df)
        elif self.prev_small_pivot == "spl":
            sp_df, spl_found, sph_index = self.calculate_small_pivot_high(df)
        else:
            sp_df = df

        self.values = sp_df.copy()

    def calculate_small_pivot_high(self, df):
        ind = df.index

        for i in range(self.prev_small_pivot_idx, len(df)):
            anchor_close = df['close'][i]
            anchor_low = df['low'][i]

            for j in range(i + 1, len(df)):
                bar1_close = df['close'][j]
                bar1_low = df['low'][j]

                # Do not look for candles where bar1 itself does not meet the criteria
                if bar1_close < anchor_close and bar1_low < anchor_low:
                    for k in range(j + 1, len(df)):
                        bar2_close = df['close'][k]
                        bar2_low = df['low'][k]

                        if bar2_close < anchor_close and bar2_low < anchor_low:
                            # We have found a pivot
                            df.loc[ind[i], 'small_pivot_type'] = "sph"
                            self.prev_small_pivot = "sph"
                            df.loc[ind[i], 'bar1'] = str(ind[j])
                            df.loc[ind[i], 'bar2'] = str(ind[k])
                            self.prev_small_pivot_idx = k
                            return df, True, i

        return df, False, -1

    def calculate_small_pivot_low(self, df):
        ind = df.index

        for i in range(self.prev_small_pivot_idx, len(df)):
            anchor_close = df['close'][i]
            anchor_high = df['high'][i]

            for j in range(i + 1, len(df)):
                bar1_close = df['close'][j]
                bar1_high = df['high'][j]

                # Do not look for candles where bar1 itself does not meet the criteria
                if bar1_close > anchor_close and bar1_high > anchor_high:
                    for k in range(j + 1, len(df)):
                        bar2_close = df['close'][k]
                        bar2_high = df['high'][k]

                        if bar2_close > anchor_close and bar2_high > anchor_high:
                            # We have found a pivot
                            df.loc[ind[i], 'small_pivot_type'] = "spl"
                            df.loc[ind[i], 'bar1'] = str(ind[j])
                            df.loc[ind[i], 'bar2'] = str(ind[k])
                            self.prev_small_pivot = "spl"
                            self.prev_small_pivot_idx = k
                            return df, True, i

        return df, False, -1

    def plot(self):
        pass
