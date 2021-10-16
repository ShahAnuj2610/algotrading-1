import logging
import sys
from datetime import datetime

import pandas as pd
from kiteconnect import KiteTicker

from trading.constants import EXCHANGE, SUPER_TREND_STRATEGY_7_3, PARABOLIC_SAR, BACK_TEST
from trading.helpers.TicksDB import TicksDB
from trading.factory.StrategyFactory import StrategyFactory
from trading.helpers.AccessTokenHelper import AccessTokenHelper
from trading.helpers.InstrumentsHelper import InstrumentsHelper
from trading.zerodha.auth.Authorizer import Authorizer
from trading.zerodha.kite.Ticks import Ticks


def listen_to_market(kite, symbols):
    instruments_helper = InstrumentsHelper(kite, EXCHANGE)
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


def authorize():
    authorizer = Authorizer(AccessTokenHelper())
    kite = authorizer.get_authorized_kite_object()
    logging.info("Authorized with kite connect successfully")
    return kite


def start_threads_and_wait(threads):
    # We want to start at the strike of every minute
    init_time = datetime.now()
    logging.info("Sleeping {} seconds to synchronize with minutes".format(60 - init_time.second))

    # Comment me for tests!
    # time.sleep(60 - init_time.second)

    # Start all threads
    for t in threads:
        t.start()

    # Wait for all of them to finish
    for t in threads:
        t.join()


def get_ohlc_for_time(instruments_helper):
    _db = TicksDB(instruments_helper)
    _df = _db.get_ticks('APOLLOHOSP', '2021-09-28 12:35:00', '2021-09-28 12:39:00')
    _ticks = _df.loc[:, ['price']]
    resampled_df = _ticks['price'].resample('1Min').ohlc()
    resampled_df.index = pd.to_datetime(resampled_df.index)
    resampled_df = resampled_df.sort_index(ascending=True)
    print(resampled_df)
    sys.exit(0)


def trade():
    logging.basicConfig(format='%(asctime)s :: %(levelname)s :: %(message)s', level=logging.INFO)

    kite = authorize()

    logging.info("Available cash {}".format(kite.margins("equity")['net']))

    threads = []
    mode = BACK_TEST

    # threads.extend(StrategyFactory(kite, mode).get_strategies(PARABOLIC_SAR))
    threads.extend(StrategyFactory(kite, mode).get_strategies(SUPER_TREND_STRATEGY_7_3))
    # threads.append(AutoSquareOffWorker(kite))

    symbols = []
    for worker in threads:
        if hasattr(worker, 'strategy'):
            symbols.append(worker.strategy.symbol)

    # listen_to_market(kite, symbols)

    start_threads_and_wait(threads)
