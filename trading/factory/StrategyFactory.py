from abc import ABC

from trading.constants import SUPER_TREND_STRATEGY_7_3, PARABOLIC_SAR
from trading.factory.ParabolicSARStrategyFactory import ParabolicSARStrategyFactory
from trading.factory.SuperTrendStrategyFactory import SuperTrendStrategyFactory


class StrategyFactory(ABC):
    def __init__(self, kite, mode, instruments_helper):
        self.kite = kite
        self.mode = mode
        self.instruments_helper = instruments_helper
        pass

    def get_strategies(self, name):
        if name == SUPER_TREND_STRATEGY_7_3:
            return SuperTrendStrategyFactory(self.kite, self.mode, self.instruments_helper).get_strategies(name)
        elif name == PARABOLIC_SAR:
            return ParabolicSARStrategyFactory(self.kite, self.mode, self.instruments_helper).get_strategies(name)
