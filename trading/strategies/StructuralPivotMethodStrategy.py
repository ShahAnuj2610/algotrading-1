import numpy as np

from trading.constants import CHARTS_PATH
from trading.indicators.StructuralPivot import StructuralPivot
from trading.strategies.Strategy import Strategy
from trading.zerodha.kite.Period import Period
import matplotlib.pyplot as plt
import mplfinance as mpf


class StructuralPivotMethodStrategy(Strategy):
    def __init__(self, kite, symbol, **kwargs):
        # Initialise all strategy params
        self.kite = kite
        self.candle_length = 1
        self.mode = kwargs['mode']
        self.candle_interval = kwargs['candle_interval']
        self.db_path = kwargs['db_path']
        self.period = Period.MIN

        # This initialisation is necessary for the strategies to access the value
        # DO NOT remove this thinking it is redundant
        self.symbol = symbol

        # Initialise all indicators
        self.sp_indicator = StructuralPivot(self, **kwargs)

        # The order of the indicators matter
        # Ordered by dependencies
        super().__init__(kite,
                         symbol,
                         [
                             self.sp_indicator
                         ],
                         **kwargs)

        self.previous_position = "na"
        self.previous_pivot = "na"
        self.all_pivots = []
        self.significant_pivots = []
        self.previous_spl = {
            'candle_time': "na",
            'value': 0.0
        }
        self.previous_sph = {
            'candle_time': "na",
            'value': 0.0
        }

    def do_act(self, candle_time):
        pivots = self.sp_indicator.get_all_values()

        if pivots.empty:
            # Enough candle have not formed yet
            return

        recent_close = pivots['close'].iloc[-1]

        if self.previous_sph['value'] == 0.0 or self.previous_spl['value'] == 0.0:
            # We need to find the first two pivots to start with
            # Until we find them, we wont take any all_positions
            self.initialise_pivots(pivots)
        elif self.previous_pivot == "sph":
            # Look for last SPL closing below the most recent SPL
            # Most recent SPL is self.previous_spl and the last SPL is the last value in pivots df
            # If these two values are the same, it means we are still looking for out a new SPL
            last_spl, last_spl_candle_time = self.get_last_spl(pivots)

            if self.can_go_short(recent_close, pivots):
                # We have not found a new SPL!!
                # But we have broken the previous SPL. Hence we are going short
                self.stop_and_reverse_enter_short_position(candle_time, recent_close)

            if last_spl != self.previous_spl['value']:
                if last_spl_candle_time == self.previous_spl['candle_time']:
                    raise ValueError("Two SPLs cannot have the same candle time")

                # We have found a new SPL
                self.previous_spl = {
                    'candle_time': str(last_spl_candle_time),
                    'value': last_spl
                }
                self.previous_pivot = "spl"

                if self.can_go_long(recent_close, pivots):
                    # There can be cases where a new pivot is formed and we breach the previous pivot
                    self.stop_and_reverse_enter_long_position(candle_time, recent_close)
        elif self.previous_pivot == "spl":
            # Look for last SPH closing above the most recent SPH
            # Most recent SPL is self.previous_sph and the last SPH is the last value in pivots df
            # If these two values are the same, it means we are still looking for out a new SPH
            last_sph, last_sph_candle_time = self.get_last_sph(pivots)

            if self.can_go_long(recent_close, pivots):
                # We have not found a new SPH!!
                # But we have broken the previous SPH. Hence we are going long
                self.stop_and_reverse_enter_long_position(candle_time, recent_close)

            if last_sph != self.previous_sph['value']:
                if last_sph_candle_time == self.previous_spl['candle_time']:
                    raise ValueError("Two SPLHs cannot have the same candle time")

                    # We have found a new SPL
                self.previous_sph = {
                    'candle_time': str(last_sph_candle_time),
                    'value': last_sph
                }
                self.previous_pivot = "sph"

                if self.can_go_short(recent_close, pivots):
                    # There can be cases where a new pivot is formed and we breach the previous pivot
                    self.stop_and_reverse_enter_short_position(candle_time, recent_close)

    def initialise_pivots(self, df):
        spl_df = df[df.small_pivot_type == "spl"]
        if not spl_df.empty:
            if self.previous_spl['value'] != 0.0 and self.previous_spl['value'] != spl_df['low'].iloc[-1]:
                raise ValueError("SPL is already initialised")

            self.previous_spl = {
                'candle_time': spl_df.index[-1],
                'value': spl_df['low'].iloc[-1]
            }

            self.all_pivots.append(self.previous_spl)
            self.previous_pivot = "spl"

        sph_df = df[df.small_pivot_type == "sph"]
        if not sph_df.empty:
            if self.previous_sph['value'] != 0.0 and self.previous_sph['value'] != sph_df['high'].iloc[-1]:
                raise ValueError("SPH is already initialised")

            self.previous_sph = {
                'candle_time': sph_df.index[-1],
                'value': sph_df['high'].iloc[-1]
            }

            self.all_pivots.append(self.previous_sph)
            self.previous_pivot = "sph"

    def get_last_spl(self, df):
        spl_df = df[df.small_pivot_type == "spl"].tail(1)
        last_spl = spl_df['low'].iloc[-1]
        last_spl_candle_time = spl_df.index[-1]

        return last_spl, last_spl_candle_time

    def get_last_sph(self, df):
        sph_df = df[df.small_pivot_type == "sph"].tail(1)
        last_sph = sph_df['high'].iloc[-1]
        last_sph_candle_time = sph_df.index[-1]

        return last_sph, last_sph_candle_time

    def can_go_short(self, recent_close, df):
        last_spl, last_spl_candle_time = self.get_last_spl(df)

        if recent_close < last_spl and len(self.short_positions) == 0:
            return True

        return False

    def can_go_long(self, recent_close, df):
        last_sph, last_sph_candle_time = self.get_last_sph(df)

        if recent_close > last_sph and len(self.long_positions) == 0:
            return True

        return False

    def plot(self):
        indicator_values = self.sp_indicator.get_all_values()

        ohlc_frame = indicator_values[['open', 'high', 'low', 'close']].copy()
        ohlc_frame.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close'}, inplace=True)
        ohlc_frame.index.name = 'Date'

        fname = CHARTS_PATH + self.symbol + "_" + str(self.opening_time.date()) + ".jpeg"
        fig, axlist = mpf.plot(ohlc_frame,
                               type='candle',
                               style='yahoo',
                               returnfig=True
                               )

        ind = indicator_values.index
        for i in range(len(indicator_values)):
            if indicator_values['small_pivot_type'][i] == "sph":
                axlist[0].annotate('SPH', xy=(i, indicator_values['high'][i]))
            elif indicator_values['small_pivot_type'][i] == "spl":
                axlist[0].annotate('SPL', xy=(i, indicator_values['low'][i]))

            order_index = self.orders.order_book.index
            for j in range(len(self.orders.order_book)):
                if ind[i] == order_index[j]:
                    axlist[0].annotate(self.orders.order_book['action'][j], xy=(i, self.orders.order_book['price'][j]))

        fig.savefig(CHARTS_PATH + self.symbol + "_" + str(self.opening_time.date()) + ".jpeg")

