import logging
import traceback

import pandas as pd
from sqlalchemy import create_engine

from trading.constants import SCREENER_DB_PATH, PARABOLIC_SAR, BACK_TEST, SETUP
from trading.strategies.ParabolicSARStrategy import ParabolicSARStrategy
from trading.workers.BackTestStrategyRunner import BackTestStrategyRunner
from trading.workers.LiveStrategyRunner import LiveStrategyRunner


class ParabolicSARStrategyFactory:
    """
    Constructs a parabolic SAR strategy based on the desired candle length
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
        Get parabolic SAR strategy for each applicable symbol with the desired candle length
        :param name: Name of the strategy
        :return: a list of strategy worker threads that will run the strategy for each symbol
        """
        try:
            cnx = create_engine(f"sqlite:///" + SCREENER_DB_PATH).connect()
            df = pd.read_sql_table("PreviousDayMaxMover", cnx)
            df = df[df['Symbol'].apply(lambda s: not s[0].isdigit())]
            df = df[df['close'] > 20]
            df = df.sort_values(by=['Move'], ascending=False)
            # Just pick the top 5 moving stocks
            # The direction is not mentioned. Hence we can go long or short
            # It is up to the strategy
            df = df.head(5)
            symbols = df['Symbol'].to_list()
            if not symbols:
                logging.error("There was an error fetching symbols list from the screener database")
                symbols = ["TVSMOTOR"]
        except Exception as e:
            # If there is any exception thrown, we will stick to some default stock so that the strategy is running
            logging.error("There was an error fetching symbols list from the screener database")
            print(e)
            print(traceback.format_exc())
            symbols = ["TVSMOTOR"]

        strategy_workers = []

        symbols = symbols[:1]

        for symbol in symbols:
            if name == PARABOLIC_SAR:
                strategy_workers.append(self.get_strategy_runner(ParabolicSARStrategy(self.kite, symbol,
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
