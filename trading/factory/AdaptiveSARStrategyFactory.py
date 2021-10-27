from trading.constants import BACK_TEST, SETUP, VOLATILITY_SYSTEM_STRATEGY
from trading.screener.PreviousDayMaxMover import PreviousDayMaxMover
from trading.strategies.AdaptiveSARStrategy import AdaptiveSARStrategy
from trading.workers.BackTestStrategyRunner import BackTestStrategyRunner
from trading.workers.LiveStrategyRunner import LiveStrategyRunner


class AdaptiveSARStrategyFactory:
    """
    Constructs a Volatility accommodative SAR strategy based on the desired candle length
    """
    def __init__(self, kite, mode, **kwargs):
        self.kite = kite
        self.mode = mode
        self.instruments_helper = kwargs['instruments_helper']
        self.orders = kwargs['orders']
        self.opening_time = kwargs['opening_time']
        self.db_path = kwargs['db_path']

    def get_strategies(self, name):
        """
        Get strategy for each applicable symbol with the desired candle length
        :param name: Name of the strategy
        :return: a list of strategy worker threads that will run the strategy for each symbol
        """
        symbols = PreviousDayMaxMover(1, self.kite).get_results()
        symbols = ['TATAPOWER']
        strategy_workers = []

        for symbol in symbols:
            if name == VOLATILITY_SYSTEM_STRATEGY:
                strategy_workers.append(self.get_strategy_runner(AdaptiveSARStrategy(self.kite, symbol,
                                                                                     orders=self.orders,
                                                                                     db_path=self.db_path,
                                                                                     candle_interval=3,
                                                                                     instruments_helper=self.instruments_helper,
                                                                                     opening_time=self.opening_time,
                                                                                     mode=self.mode)))

        return strategy_workers

    def get_strategy_runner(self, strategy):
        if self.mode == BACK_TEST or self.mode == SETUP:
            return BackTestStrategyRunner(self.kite, strategy)
        else:
            return LiveStrategyRunner(self.kite, strategy)
