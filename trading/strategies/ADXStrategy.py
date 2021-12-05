from trading.indicators.ADX import ADX
from trading.indicators.DX import DX
from trading.indicators.TrueRange import TrueRange
from trading.strategies.Strategy import Strategy
from trading.zerodha.kite.Period import Period


class ADXStrategy(Strategy):
    def __init__(self, kite, symbol, **kwargs):
        # Initialise all strategy params
        self.kite = kite
        self.candle_length = 14
        self.mode = kwargs['mode']
        self.candle_interval = kwargs['candle_interval']
        self.db_path = kwargs['db_path']
        self.period = Period.MIN

        # This initialisation is necessary for the strategies to access the value
        # DO NOT remove this thinking it is redundant
        self.symbol = symbol

        # Initialise all indicators
        self.true_range_indicator = TrueRange(self, **kwargs)
        self.dx_indicator = DX(self, **kwargs)
        self.adx_indicator = ADX(self, **kwargs)

        # The order of the indicators matter
        # Ordered by dependencies
        super().__init__(kite,
                         symbol,
                         [
                             self.true_range_indicator,
                             self.dx_indicator,
                             self.adx_indicator
                         ],
                         **kwargs)

    def do_act(self, candle_time):
        pass

    def get_true_range_indicator(self):
        return self.true_range_indicator

    def get_dx_indicator(self):
        return self.dx_indicator


