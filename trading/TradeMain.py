import logging
import sqlite3
import sys
import time
import traceback
from datetime import datetime

from kiteconnect import KiteTicker

from trading.constants import EXCHANGE, LIVE, TICKS_DB_PATH, PARABOLIC_SAR, SUPER_TREND_STRATEGY_7_3
from trading.factory.StrategyFactory import StrategyFactory
from trading.helpers.InstrumentsHelper import InstrumentsHelper
from trading.workers.AutoSqaureOffWorker import AutoSquareOffWorker
from trading.zerodha.kite.Ticks import Ticks


def listen_to_market(kite, symbols, instruments_helper):
    ticks = Ticks(symbols, instruments_helper)
    on_ticks = ticks.on_ticks

    on_connect = ticks.on_connect
    do_listen_to_market(kite, on_ticks, on_connect)


def do_listen_to_market(kite, on_ticks, on_connect):
    logging.info("Connecting to market")
    kite_ticker = KiteTicker(kite.api_key, kite.access_token)

    kite_ticker.on_ticks = on_ticks
    kite_ticker.on_connect = on_connect
    kite_ticker.connect(threaded=True)
    logging.info("Started listening to market")


def start_threads_and_wait(threads):
    # We want to start at the strike of every minute
    init_time = datetime.now()
    logging.info("Sleeping {} seconds to synchronize with minutes".format(60 - init_time.second))

    # Comment me for tests!
    time.sleep(60 - init_time.second)

    # Start all threads
    for t in threads:
        t.start()

    # Wait for all of them to finish
    for t in threads:
        t.join()


def initialize_symbol_for_live_trade(symbol):
    db = sqlite3.connect(TICKS_DB_PATH)

    c = db.cursor()
    table_name = symbol  # + "-" + str(self.suffix)
    c.execute(
        "CREATE TABLE IF NOT EXISTS {} (ts datetime primary key, price real(15,5), volume integer)".format(
            table_name))
    try:
        db.commit()
    except Exception as e:
        print(e)
        print(traceback.format_exc())
        sys.exit(1)

    db.close()


def initialize_symbols_for_live_trade(symbols):
    for symbol in symbols:
        initialize_symbol_for_live_trade(symbol)


def trade(kite):
    instruments_helper = InstrumentsHelper(kite, EXCHANGE)

    threads = []
    mode = LIVE

    threads.extend(StrategyFactory(kite, mode, instruments_helper).get_strategies(PARABOLIC_SAR))
    threads.extend(StrategyFactory(kite, mode, instruments_helper).get_strategies(SUPER_TREND_STRATEGY_7_3))
    threads.append(AutoSquareOffWorker(kite))

    # Collect all the symbols that our strategies want to act on
    # Then, listen to the market for those symbols
    symbols = []
    for worker in threads:
        if hasattr(worker, 'strategy'):
            symbols.append(worker.strategy.symbol)

    # Different strategies can run for the same symbol
    unique_symbols = list(set(symbols))

    initialize_symbols_for_live_trade(unique_symbols)
    logging.info("Db for symbols {} initialised in {}".format(','.join(unique_symbols), TICKS_DB_PATH))
    listen_to_market(kite, symbols, instruments_helper)

    start_threads_and_wait(threads)
