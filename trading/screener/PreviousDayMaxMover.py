import logging

import pandas as pd

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

