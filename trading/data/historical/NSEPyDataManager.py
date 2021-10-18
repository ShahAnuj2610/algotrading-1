import logging

from nsepy import get_history
from trading.zerodha.kite.Retry import retry


class NSEPyDataManager:
    """
    Gets historical OHLC data for the given symbol from NSE website. It uses NSEpy library to get the data
    """
    def __init__(self, **kwargs):
        super().__init__()

    @retry(tries=5, delay=2, backoff=2)
    def get_data(self, symbol, start, end):
        from_date = start.date()
        to_date = end.date()

        logging.info("Fetching historical data from NSEpy for {} from {} till {}".format(symbol, from_date, to_date))
        return get_history(symbol=symbol, start=from_date, end=to_date)
