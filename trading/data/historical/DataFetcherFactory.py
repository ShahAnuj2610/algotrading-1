from trading.data.historical.NSEDataFetcher import NSEDataFetcher


class DataFetcherFactory:
    """
    Factory class which constructs a historical data (i.e OHLC) fetcher based on the given exchange
    For example if the exchange is NSE, it uses NSEpy library which talks to NSE website and scraps OHLC data
    for the given time
    """
    def __init__(self, store_helper):
        self.store_helper = store_helper

    def get_object(self, exchange):
        if exchange == "NSE":
            return NSEDataFetcher(self.store_helper)
