import logging
import sqlite3

import pandas as pd
from sqlalchemy import create_engine

from trading.constants import BACK_TEST_OHLC_DB_PATH, CSV_PATH
from trading.zerodha.kite.Period import Period
from trading.zerodha.kite.Retry import retry


class KiteHistoricalDataManager:
    """
    Gets historical OHLC data for the given symbol from Zerodha's historical api.
    Requires a valid kite object and symbols-instruments map
    """

    def __init__(self, kite, **kwargs):
        self.kite = kite
        self.instruments_helper = kwargs['instruments_helper']

        self.period = kwargs['period']
        self.candle_interval = kwargs['candle_interval']
        self.interval = self.get_interval()

        self.table_name_suffix = "_" + str(self.candle_interval) + "_" + self.period.name

        super().__init__()

    @retry(tries=5, delay=2, backoff=2)
    def get_data_from_kite(self, symbol, start, end):
        from_date = start.date()
        to_date = end.date()

        instrument = self.instruments_helper.get_instrument_token_from_symbol(symbol)

        # This could be because the sample set might contain a stock that is not listed in the exchange
        # the program assumes
        # For now we focus only on one exchange
        # TODO: Make this code exchange agnostic
        if not instrument:
            return pd.DataFrame()

        logging.debug("Fetching historical data from Zerodha for {} / {} from {} till {}".
                      format(symbol, instrument, from_date, to_date))

        df = pd.DataFrame(
            self.kite.historical_data(instrument, start, end, self.interval))

        if df.empty:
            return pd.DataFrame()

        df['date'] = df['date'].dt.tz_localize(None)
        df = df.rename(columns={'date': 'ts'})
        df = df.set_index('ts')
        return df

    @retry(tries=5, delay=2, backoff=2)
    def put_data(self, symbol, start, end):
        df = self.get_data_from_kite(symbol, start, end)

        if df.empty:
            # This could be a non trading day
            return False

        engine = create_engine(f"sqlite:///" + BACK_TEST_OHLC_DB_PATH)
        df.to_sql(symbol + self.table_name_suffix, engine, if_exists='replace')
        engine.dispose()

        return True

    @retry(tries=5, delay=2, backoff=2)
    def put_data_to_csv(self, file_name, symbol, start, end):
        df = self.get_data_from_kite(symbol, start, end)

        if df.empty:
            return

        df.to_csv(file_name)

    @retry(tries=5, delay=2, backoff=2)
    def get_data(self, symbol, start, end):
        logging.debug("Fetching ticks data from OHLC db for {} from {} till {}".format(symbol, start, end))

        query = "SELECT * FROM {} where ts >= '{}' and ts < '{}'".format(symbol + self.table_name_suffix, start, end)

        db = sqlite3.connect(BACK_TEST_OHLC_DB_PATH)
        data = pd.read_sql_query(query, db)
        db.close()

        data = data.set_index(['ts'])
        data.index = pd.to_datetime(data.index)
        return data

    def close(self):
        pass

    def get_interval(self):
        if self.period == Period.MIN:
            if self.candle_interval == 1:
                return 'minute'
            else:
                return str(self.candle_interval) + 'minute'
        elif self.period == Period.DAY:
            return 'day'
