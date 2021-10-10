from abc import ABC, abstractmethod

from trading.constants import SUPER_TREND_STRATEGY_7_3
from trading.factory.SuperTrendStrategyFactory import SuperTrendStrategyFactory


class StrategyFactory(ABC):
    def __init__(self, kite):
        self.kite = kite
        pass

    def get_strategies(self, name):
        if name == SUPER_TREND_STRATEGY_7_3:
            return SuperTrendStrategyFactory(self.kite).get_strategies(name)
