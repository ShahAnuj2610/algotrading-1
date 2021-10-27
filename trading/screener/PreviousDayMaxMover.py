import logging
import traceback

import pandas as pd
from sqlalchemy import create_engine

from trading.constants import SCREENER_DB_PATH
from trading.screener.StockScreener import StockScreener
from trading.zerodha.kite.TimeSequencer import get_previous_trading_day


class PreviousDayMaxMover(StockScreener):
    """
    Identifies stocks that has moved to a good extent only in their previous day (i.e abs(close - open) is greater)
    """
    def __init__(self, symbols_to_filter, kite):
        super().__init__(kite)

        # Number of symbols to return
        self.symbols_to_filter = symbols_to_filter

    def do_screen(self, symbols_df):
        """
        Screens for stocks whose most recent trading move is significantly higher
        :return: Pandas dataframe containing the filtered symbols info OHLC data
        """
        previous_trading_day = get_previous_trading_day()
        df = pd.DataFrame()

        for symbol in symbols_df:
            logging.info("Screening for stock {}".format(symbol))

            data = self.historical_data_manager.get_data_from_kite(
                symbol,
                previous_trading_day.replace(hour=9, minute=15, second=0, microsecond=0),
                previous_trading_day.replace(hour=15, minute=30, second=0, microsecond=0))

            if data.empty:
                continue

            data['Symbol'] = symbol
            data = data[['Symbol', 'open', 'high', 'low', 'close', 'volume']]
            data = data.reset_index(level=0)
            df = df.append(data)

        df = df.set_index('Symbol')
        df['Move'] = ((abs(df['close'] - df['open'])) / df['open']) * 100.0
        df = df.sort_values(by=['Move'], ascending=False)
        df = df.head(self.symbols_to_filter)
        return df

    def get_results(self):
        try:
            cnx = create_engine(f"sqlite:///" + SCREENER_DB_PATH).connect()
            df = pd.read_sql_table(self.__class__.__name__, cnx)
            df = df[df['Symbol'].apply(lambda s: not s[0].isdigit())]
            df = df[df['close'] > 20]
            df = df.sort_values(by=['Move'], ascending=False)
            # Just pick the top 5 moving stocks
            # The direction is not mentioned. Hence we can go long or short
            # It is up to the strategy
            df = df.head(self.symbols_to_filter)
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

        return symbols

