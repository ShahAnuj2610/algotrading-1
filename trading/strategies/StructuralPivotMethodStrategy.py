from trading.indicators.StructuralPivot import StructuralPivot
from trading.strategies.Strategy import Strategy
from trading.zerodha.kite.Period import Period


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

    def act(self, candle_time):
        pivots = self.sp_indicator.get_all_values()
        recent_close = self.sp_indicator.get_previous_indicator_value(candle_time)

        if self.previous_sph['value'] == 0.0 or self.previous_spl['value'] == 0.0:
            # We need to find the first two pivots to start with
            # Until we find them, we wont take any positions
            self.initialise_pivots(pivots)
        elif self.previous_pivot == "sph":
            # Look for last SPL closing below the most recent SPL
            # Most recent SPL is self.previous_spl and the last SPL is the last value in pivots df
            # If these two values are the same, it means we are still looking for out a new SPL
            spl_df = pivots[pivots.small_pivot_type == "spl"].tail(1)
            last_spl = spl_df['close'].iloc[-1]
            last_spl_candle_time = spl_df['ts'].iloc[-1]

            if recent_close < last_spl and len(self.short_positions == 0):
                # We have not found a new SPL
                # But we have broken the previous SPL. Hence we are going short
                self.stop_and_reverse_enter_short_position(recent_close, candle_time)

            if last_spl != self.previous_spl['value']:
                if last_spl_candle_time == self.previous_spl['candle_time']:
                    raise ValueError("Two SPLs cannot have the same candle time")

                if last_spl < self.previous_spl['value'] and len(self.short_positions == 0):
                    raise ValueError("Trying to set a lower SPL when there is no open short position. Did we miss the "
                                     "train??")

                # We have found a new SPL
                self.previous_spl = {
                    'candle_time': str(last_spl_candle_time),
                    'value': last_spl
                }
                self.previous_pivot = "spl"
        elif self.previous_pivot == "spl":
            # Look for last SPH closing above the most recent SPH
            # Most recent SPL is self.previous_sph and the last SPH is the last value in pivots df
            # If these two values are the same, it means we are still looking for out a new SPH
            sph_df = pivots[pivots.small_pivot_type == "sph"].tail(1)
            last_sph = sph_df['close'].iloc[-1]
            last_sph_candle_time = sph_df['ts'].iloc[-1]

            if recent_close > last_sph and len(self.long_positions == 0):
                # We have not found a new SPH!!
                # But we have broken the previous SPH. Hence we are going long
                self.stop_and_reverse_enter_long_position(recent_close, candle_time)

            if last_sph != self.previous_sph['value']:
                if last_sph_candle_time == self.previous_spl['candle_time']:
                    raise ValueError("Two SPLHs cannot have the same candle time")

                if last_sph > self.previous_sph['value'] and len(self.long_positions == 0):
                    raise ValueError("Trying to set a higher SPH when there is no open long position. Did we miss the "
                                     "train??")

                    # We have found a new SPL
                self.previous_sph = {
                    'candle_time': str(last_sph_candle_time),
                    'value': last_sph
                }
                self.previous_pivot = "sph"

    def initialise_pivots(self, df):
        spl_df = df[df.small_pivot_type == "spl"]
        if not spl_df.empty:
            if self.previous_spl['value'] != 0.0:
                raise ValueError("SPL is already initialised")

            self.previous_spl = {
                'candle_time': spl_df['ts'].iloc[-1],
                'value': spl_df['close'].iloc[-1]
            }

            self.all_pivots.append(self.previous_spl)
            self.previous_pivot = "spl"

        sph_df = df[df.small_pivot_type == "sph"]
        if not sph_df.empty:
            if self.previous_sph['value'] == 0.0:
                raise ValueError("SPH is already initialised")

            self.previous_sph = {
                'candle_time': sph_df['ts'].iloc[-1],
                'value': sph_df['close'].iloc[-1]
            }

            self.all_pivots.append(self.previous_sph)
            self.previous_pivot = "sph"
