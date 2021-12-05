from trading.constants import PARABOLIC_SAR, BACK_TEST, SETUP
from trading.screener.PreviousDayMaxMover import PreviousDayMaxMover
from trading.strategies.ParabolicSARStrategy import ParabolicSARStrategy
from trading.strategies.StructuralPivotMethodStrategy import StructuralPivotMethodStrategy
from trading.workers.BackTestStrategyRunner import BackTestStrategyRunner
from trading.workers.LiveStrategyRunner import LiveStrategyRunner


class StructuralPivotMethodStrategyFactory:
    """
    Constructs a Structural Pivot Method strategy based on the desired candle length
    """

    def __init__(self, kite, mode, **kwargs):
        self.kite = kite
        self.mode = mode
        self.instruments_helper = kwargs['instruments_helper']
        self.opening_time = kwargs['opening_time']
        self.db_path = kwargs['db_path']
        self.orders = kwargs['orders']
        self.candle_interval = kwargs['candle_interval']

    def get_strategies(self, name):
        """
        Get Structural Pivot Method strategy for each applicable symbol with the desired candle length
        :param name: Name of the strategy
        :return: a list of strategy worker threads that will run the strategy for each symbol
        """
        symbols = ['SBIN']

        strategy_workers = []

        for symbol in symbols:
            strategy_workers.append(self.get_strategy_runner(StructuralPivotMethodStrategy(self.kite, symbol,
                                                                                           orders=self.orders,
                                                                                           db_path=self.db_path,
                                                                                           candle_interval=self.candle_interval,
                                                                                           instruments_helper=self.instruments_helper,
                                                                                           opening_time=self.opening_time,
                                                                                           # If stateless is True, then the strategy will not
                                                                                           # consider previous trading session's indicator values
                                                                                           stateless=True,
                                                                                           mode=self.mode)))

        return strategy_workers

    def get_strategy_runner(self, strategy):
        if self.mode == BACK_TEST or self.mode == SETUP:
            return BackTestStrategyRunner(self.kite, strategy)
        else:
            return LiveStrategyRunner(self.kite, strategy)
