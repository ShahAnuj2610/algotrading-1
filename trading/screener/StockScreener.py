from abc import ABC, abstractmethod

from trading.constants import STORE_PATH, EXCHANGE
from trading.data.historical.DataFetcherFactory import DataFetcherFactory
from trading.data.symbols.SymbolsDataFetcherFactory import SymbolsDataFetcherFactory
from trading.helpers.StoreHelper import StoreHelper


class StockScreener(ABC):
    """
    Class to screen stocks on which strategies will be applied.
    Each strategy will have different criteria for selecting stocks and they should use the appropriate screener
    """
    def __init__(self):
        self.store_helper = StoreHelper(STORE_PATH)
        self.data_fetcher = SymbolsDataFetcherFactory(self.store_helper).get_object(EXCHANGE)
        self.historical_data_fetcher = DataFetcherFactory(self.store_helper).get_object(EXCHANGE)
        # 500 random symbols from the desired exchange
        self.symbols_sample_space = 500
        pass

    def _type(self):
        return self.__class__.__name__

    def screen(self):
        """
        Screens for individual conditions determined by the strategies
        :return: Pandas dataframe containing OHLC for all the stocks that have passed the filter
        """
        symbols_df = self.data_fetcher.get_n_symbols(self.symbols_sample_space)
        return self.do_screen(symbols_df)

    @abstractmethod
    def do_screen(self, symbols_df):
        """
        Screens for individual conditions determined by the strategies
        :param symbols_df The dataframe obtained by talking to the data source
        :return: Pandas dataframe containing OHLC for all the stocks that have passed the filter
        """
        pass