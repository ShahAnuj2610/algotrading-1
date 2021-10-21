from trading.constants import SCREEN, LIVE, BACK_TEST, SETUP
from trading.data.historical.KiteHistoricalDataManager import KiteHistoricalDataManager
from trading.data.live.TicksDataManager import TicksDataManager


class DataManagerFactory:
    """
    Factory class which constructs a historical data (i.e OHLC) fetcher based on the given exchange
    For example if the exchange is NSE, it uses NSEpy library which talks to NSE website and scraps OHLC data
    for the given time
    """
    def __init__(self, kite, mode):
        self.kite = kite
        self.mode = mode

    def get_object(self, **kwargs):
        if self.mode == LIVE:
            return TicksDataManager(**kwargs)
        elif self.mode == BACK_TEST or self.mode == SCREEN or self.mode == SETUP:
            return KiteHistoricalDataManager(self.kite, **kwargs)
        else:
            raise ValueError("Unknown mode {}".format(self.mode))
