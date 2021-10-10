import pandas as pd

from trading.screener.StockScreener import StockScreener
from trading.zerodha.kite.TimeSequencer import get_previous_trading_day


class PreviousDayMaxMover(StockScreener):
    """
    Identifies stocks that has moved to a good extent only in their previous day (i.e abs(close - open) is greater)
    """
    def __init__(self, symbols_to_filter):
        super().__init__()

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
            data = self.historical_data_fetcher.get_data(symbol, previous_trading_day, previous_trading_day)
            data = data[['Symbol', 'Open', 'High', 'Low', 'Close', 'Volume']]
            data = data.reset_index(level=0)
            df = df.append(data)

        df = df.set_index('Symbol')
        df['Move'] = ((abs(df['Close'] - df['Open'])) / df['Open']) * 100.0
        df = df.sort_values(by=['Move'], ascending=False)
        df = df.head(self.symbols_to_filter)
        return df

