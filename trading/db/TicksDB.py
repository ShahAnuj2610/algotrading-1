import datetime
import logging
import sqlite3
import traceback

import pandas as pd

from trading.zerodha.kite.Retry import retry


class TicksDB:
    def __init__(self, ticks_db_path, instruments_db):
        self.db = sqlite3.connect(ticks_db_path)
        self.instruments_db = instruments_db

    def insert_ticks(self, ticks):
        c = self.db.cursor()
        for tick in ticks:
            try:
                tok = self.instruments_db.get_symbol_from_instrument_token(tick['instrument_token'])
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
        query = "SELECT * FROM {} where ts >= '{}' and ts < '{}'".format(symbol, start_time, end_time)
        # query = "SELECT * FROM {} ORDER BY ts DESC LIMIT 2000".format(symbol)
        data = pd.read_sql_query(query, self.db)
        data = data.set_index(['ts'])
        data.index = pd.to_datetime(data.index)
        return data

    def close(self):
        self.db.close()
