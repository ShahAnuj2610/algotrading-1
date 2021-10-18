from trading.indicators.Indicator import Indicator


class ParabolicSAR(Indicator):
    def __init__(self, strategy, **kwargs):
        super().__init__(self.__class__.__name__, strategy, **kwargs)

        self.af = 0.02
        self.max_af = 0.20

    def do_calculate_lines(self, candle_time):
        sar_df = self.get_previous_indicator_value(candle_time)

        if sar_df.empty:
            ticks_df = self.get_data(candle_time)
            self.calculate_sar(ticks_df, candle_time)
            return

        ticks_df = self.get_data_for_time(candle_time)

        df = sar_df.append(ticks_df)
        self.validate_candles_and_throw(df, reversed(self.get_n_candle_sequence(2, candle_time)))

        if df['color'][0] == "green":
            self.calculate_sar_from_long_trade(df, candle_time)
        else:
            self.calculate_sar_from_short_trade(df, candle_time)

    def calculate_sar_from_short_trade(self, df_in, candle_time):
        df = df_in.copy()

        ind = df.index
        for i in range(1, len(df)):
            # Before making further calculations, check if the high has breached SAR that was calculated previously
            # The SAR value that was obtained by tailing self.df.values is the SAR that was already calculated for
            # this candle

            # If current high greater than SAR set for today, then we are going long
            if df['high'][i] > df[self.indicator_name][i - 1]:
                # Reset acceleration factor
                self.af = 0.02

                df.loc[ind[i], 'EP'] = df['high'][i]

                psar = df['EP'][i - 1]
                df.loc[ind[i], self.indicator_name] = psar + (self.af * (df['EP'][i] - psar))
                df.loc[ind[i], 'AF'] = self.af
                df.loc[ind[i], 'color'] = "green"
                break

            # Find Extreme Price
            if df['low'][i] < df['EP'][i - 1]:
                # If a new high was made, then the acceleration factor has to increase two fold
                self.af = self.af + 0.02

                # If the acceleration factor increases beyond a threshold, then limit it
                if self.af > self.max_af:
                    self.af = self.max_af
                df.loc[ind[i], 'EP'] = df['low'][i]
            else:
                df.loc[ind[i], 'EP'] = df['EP'][i - 1]

            df.loc[ind[i], 'color'] = df['color'][i - 1]
            psar = df[self.indicator_name][i - 1]
            df.loc[ind[i], 'AF'] = self.af
            df.loc[ind[i], self.indicator_name] = psar - (self.af * (psar - df['EP'][i]))

        self.store_indicator_value(df.tail(1), candle_time)

    def calculate_sar_from_long_trade(self, df_in, candle_time):
        df = df_in.copy()

        ind = df.index
        for i in range(1, len(df)):
            # Before making further calculations, check if the low has breached SAR that was calculated previously
            # The SAR value that was obtained by tailing self.df.values is the SAR that was already calculated for
            # this candle

            # If current low less than SAR set for today, then we are going short
            if df['low'][i] < df[self.indicator_name][i - 1]:
                # Reset acceleration factor
                self.af = 0.02

                df.loc[ind[i], 'EP'] = df['low'][i]

                psar = df['EP'][i - 1]
                df.loc[ind[i], self.indicator_name] = psar - (self.af * (psar - df['EP'][i]))
                df.loc[ind[i], 'AF'] = self.af
                df.loc[ind[i], 'color'] = "red"
                break

            # Find Extreme Price
            if df['high'][i] > df['EP'][i - 1]:
                # If a new high was made, then the acceleration factor has to increase two fold
                self.af = self.af + 0.02

                # If the acceleration factor increases beyond a threshold, then limit it
                if self.af > self.max_af:
                    self.af = self.max_af
                df.loc[ind[i], 'EP'] = df['high'][i]
            else:
                df.loc[ind[i], 'EP'] = df['EP'][i - 1]

            df.loc[ind[i], 'color'] = df['color'][i - 1]
            psar = df[self.indicator_name][i - 1]
            df.loc[ind[i], 'AF'] = self.af
            df.loc[ind[i], self.indicator_name] = psar + (self.af * (df['EP'][i] - psar))

        self.store_indicator_value(df.tail(1), candle_time)

    def calculate_sar(self, df_in, candle_time):
        df = self.calculate_base_params(df_in)
        self.store_indicator_value(df.tail(1), candle_time)

    def calculate_base_params(self, df_in):
        df = df_in.copy()

        # Extreme Price

        # The starting value is a guess
        if df['high'][0] < df['high'][1]:
            # We are in uptrend
            df['EP'] = df['high']
            psar = min(df['low'][0], df['low'][1])
            df[self.indicator_name] = psar + (self.af * (df['EP'] - psar))
            df['color'] = "green"
            df['AF'] = self.af
        else:
            # We are in down trend
            df['EP'] = df['low']
            psar = max(df['high'][0], df['high'][1])
            df[self.indicator_name] = psar - (self.af * (psar - df['EP']))
            df['color'] = "red"
            df['AF'] = self.af

        return df
