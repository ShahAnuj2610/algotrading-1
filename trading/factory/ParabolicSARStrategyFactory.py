import logging
import traceback

import pandas as pd
from sqlalchemy import create_engine

from trading.constants import SCREENER_DB_PATH, PARABOLIC_SAR
from trading.strategies.ParabolicSARStrategy import ParabolicSARStrategy
from trading.workers.StrategyRunner import StrategyRunner


class ParabolicSARStrategyFactory:
    """
    Constructs a parabolic SAR strategy based on the desired candle length
    """
    def __init__(self, kite, mode):
        self.kite = kite
        self.mode = mode

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
            df = df[df['Close'] > 20]
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
        symbols = ["IEX"]

        for symbol in symbols:
            if name == PARABOLIC_SAR:
                strategy_workers.append(StrategyRunner(self.kite,
                                                       ParabolicSARStrategy(self.kite, symbol,
                                                                            candle_interval=1,
                                                                            mode=self.mode)))

        return strategy_workers
