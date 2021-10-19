import logging
import sqlite3
import sys
import time
import traceback
from datetime import datetime

from kiteconnect import KiteTicker

from trading.constants import EXCHANGE, BACK_TEST, LIVE, TICKS_DB_PATH, PARABOLIC_SAR, SUPER_TREND_STRATEGY_7_3
from trading.data.DataManagerFactory import DataManagerFactory
from trading.factory.StrategyFactory import StrategyFactory
from trading.helpers.InstrumentsHelper import InstrumentsHelper
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


def initialize_symbols_for_back_test(strategies, instruments_helper, start_time, end_time):
    for strategy in strategies:
        initialize_symbol_for_back_test(strategy, instruments_helper, start_time, end_time)


def initialize_symbol_for_back_test(strategy, instruments_helper, start_time, end_time):
    data_manager = DataManagerFactory(strategy.get_kite_object(), strategy.get_mode()).get_object(
                                             period=strategy.get_period(),
                                             candle_interval=strategy.get_candle_interval(),
                                             instruments_helper=instruments_helper
                                             )

    data_manager.put_data(strategy.get_symbol(), start_time, end_time)
    data_manager.close()


def trade(kite):
    logging.basicConfig(format='%(asctime)s :: %(levelname)s :: %(message)s', level=logging.INFO)

    instruments_helper = InstrumentsHelper(kite, EXCHANGE)

    threads = []
    mode = BACK_TEST
    # mode = LIVE

    # threads.extend(StrategyFactory(kite, mode, instruments_helper).get_strategies(PARABOLIC_SAR))
    threads.extend(StrategyFactory(kite, mode, instruments_helper).get_strategies(SUPER_TREND_STRATEGY_7_3))
    # threads.append(AutoSquareOffWorker(kite))

    # Collect all the symbols that our strategies want to act on
    # Then, listen to the market for those symbols
    symbols = []
    strategies = []
    for worker in threads:
        if hasattr(worker, 'strategy'):
            strategies.append(worker.strategy)
            symbols.append(worker.strategy.symbol)

    # Different strategies can run for the same symbol
    unique_symbols = list(set(symbols))

    if mode == LIVE:
        initialize_symbols_for_live_trade(unique_symbols)
        logging.info("Db for symbols {} initialised in {}".format(','.join(unique_symbols), TICKS_DB_PATH))
        listen_to_market(kite, symbols, instruments_helper)
    elif mode == BACK_TEST:
        initialize_symbols_for_back_test(
            strategies,
            instruments_helper,
            datetime.today().replace(year=2021, month=10, day=19, hour=9, minute=15, second=0, microsecond=0),
            datetime.today().replace(year=2021, month=10, day=19, hour=15, minute=30, second=0, microsecond=0)
        )

    start_threads_and_wait(threads)
