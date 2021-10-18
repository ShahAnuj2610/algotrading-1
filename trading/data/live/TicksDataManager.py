import datetime
import logging
import sqlite3
import traceback

import pandas as pd

from trading.constants import TICKS_DB_PATH
from trading.zerodha.kite.Period import Period
from trading.zerodha.kite.Retry import retry


class TicksDataManager:
    def __init__(self, **kwargs):
        self.db = sqlite3.connect(TICKS_DB_PATH)
        self.instruments_helper = kwargs['instruments_helper']

        self.period = kwargs['period']
        self.candle_interval = kwargs['candle_interval']

        if self.period == Period.MIN:
            self.resample_time = str(self.candle_interval) + 'Min'

        super().__init__()

    def insert_ticks(self, ticks):
        c = self.db.cursor()
        for tick in ticks:
            try:
                tok = self.instruments_helper.get_symbol_from_instrument_token(tick['instrument_token'])
                vals = [datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), tick['last_price'], tick['last_quantity']]
                query = "INSERT OR REPLACE INTO {} (ts,price,volume) VALUES (?,?,?)".format(tok)
                c.execute(query, vals)
            except:
                logging.error("Exception while inserting ticks: " + traceback.format_exc())
                pass
        try:
            self.db.commit()
        except Exception as e:
            print("Exception while committing ticks: " + traceback.format_exc())
            self.db.rollback()

    @retry(tries=5, delay=0.02, backoff=2)
    def get_ticks(self, symbol, start_time, end_time):
        logging.debug("Fetching ticks data from ticks db for {} from {} till {}".format(symbol, start_time, end_time))

        query = "SELECT * FROM {} where ts >= '{}' and ts < '{}'".format(symbol, start_time, end_time)
        # query = "SELECT * FROM {} ORDER BY ts DESC LIMIT 2000".format(symbol)
        data = pd.read_sql_query(query, self.db)
        data = data.set_index(['ts'])
        data.index = pd.to_datetime(data.index)
        return data

    def resample_data(self, df):
        if df.empty:
            return df

        ticks = df.loc[:, ['price']]
        resampled_df = ticks['price'].resample(self.resample_time, base=1).ohlc()
        resampled_df.index = pd.to_datetime(resampled_df.index)
        resampled_df = resampled_df.sort_index(ascending=True)
        # resampled_df.dropna(inplace=True)
        return resampled_df

    def get_data(self, symbol, start, end):
        ticks_df = self.get_ticks(symbol, start, end)

        return self.resample_data(ticks_df)

    def put_data(self, symbol, start, end):
        pass

    def close(self):
        self.db.close()
