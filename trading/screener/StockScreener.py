from abc import ABC, abstractmethod

from trading.constants import STORE_PATH, EXCHANGE, SCREEN
from trading.data.DataManagerFactory import DataManagerFactory
from trading.data.symbols.SymbolsDataFetcherFactory import SymbolsDataFetcherFactory
from trading.helpers.InstrumentsHelper import InstrumentsHelper
from trading.helpers.StoreHelper import StoreHelper
from trading.zerodha.kite.Period import Period


class StockScreener(ABC):
    """
    Class to screen stocks on which strategies will be applied.
    Each strategy will have different criteria for selecting stocks and they should use the appropriate screener
    """

    def __init__(self, kite):
        self.kite = kite
        self.store_helper = StoreHelper(STORE_PATH)
        self.data_fetcher = SymbolsDataFetcherFactory(self.store_helper).get_object(EXCHANGE)

        # The current period for screening is DAY
        self.historical_data_manager = DataManagerFactory(kite, SCREEN).get_object(period=Period.DAY,
                                                                                   candle_interval=1,
                                                                                   instruments_helper=InstrumentsHelper(
                                                                                       self.kite, EXCHANGE)
                                                                                   )
        # 500 random symbols from the desired exchange
        self.symbols_sample_space = 500
        pass

    def screen(self):
        """
        Screens for individual conditions determined by the strategies
        :return: Pandas dataframe containing OHLC for all the stocks that have passed the filter
        """
        symbols_df = self.data_fetcher.get_symbols_allowed_for_intraday()
        return self.do_screen(symbols_df)

    @abstractmethod
    def do_screen(self, symbols_df):
        """
        Screens for individual conditions determined by the strategies
        :param symbols_df The dataframe obtained by talking to the data source
        :return: Pandas dataframe containing OHLC for all the stocks that have passed the filter
        """
        pass
