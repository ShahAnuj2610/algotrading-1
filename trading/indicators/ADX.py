import pandas as pd

from trading.indicators.Indicator import Indicator


class ADX(Indicator):
    def __init__(self, strategy, **kwargs):
        self.dx = strategy.get_dx_indicator()

        super().__init__(self.__class__.__name__, strategy, **kwargs)

    def do_calculate_lines(self, candle_time):
        adx_df = self.get_previous_indicator_value(candle_time)
        if adx_df.empty:
            self.calculate_adx(candle_time)
            return

        self.calculate_adx_from_previous_value(adx_df, candle_time)

    def calculate_adx(self, candle_time):
        df = self.dx.get_lines(self.candle_length, candle_time)

        adx_df = pd.DataFrame()

        adx_df[self.indicator_name] = \
            df[self.dx.indicator_name].rolling(self.candle_length).mean()

        adx_df[self.dx.indicator_name] = df[self.dx.indicator_name]
        adx_df['PLUSDI_14'] = df['PLUSDI_14']
        adx_df['MINUSDI_14'] = df['MINUSDI_14']

        self.store_indicator_value(adx_df.tail(1), candle_time)

    def calculate_adx_from_previous_value(self, adx_df, candle_time):
        dx_df = self.dx.get_lines(1, candle_time)

        df = pd.DataFrame()
        prev_adx = adx_df[self.indicator_name][0]
        dx = dx_df[self.dx.indicator_name][0]
        new_adx = ((prev_adx * (self.candle_length - 1)) + dx) / self.candle_length

        df.loc[dx_df.index[0], 'open'] = dx_df['open'][0]
        df.loc[dx_df.index[0], 'high'] = dx_df['high'][0]
        df.loc[dx_df.index[0], 'low'] = dx_df['low'][0]
        df.loc[dx_df.index[0], 'close'] = dx_df['close'][0]
        df.loc[dx_df.index[0], 'volume'] = dx_df['volume'][0]
        df.loc[dx_df.index[0], 'PLUSDI_14'] = dx_df['PLUSDI_14'][0]
        df.loc[dx_df.index[0], 'MINUSDI_14'] = dx_df['MINUSDI_14'][0]
        df.loc[dx_df.index[0], self.dx.indicator_name] = dx_df[self.dx.indicator_name][0]
        df.loc[dx_df.index[0], self.indicator_name] = new_adx
        df.index.names = ['ts']

        self.store_indicator_value(df.tail(1), candle_time)
