import datetime
import logging

import pandas as pd

from trading.constants import BACK_TEST, SPM_STRATEGY, EXCHANGE
from trading.data.DataManagerFactory import DataManagerFactory
from trading.factory.StrategyFactory import StrategyFactory
from trading.workers.BackTestAutoSquareOffWorker import BackTestAutoSquareOffWorker
from trading.zerodha.kite.BackTestOrders import BackTestOrders
from trading.zerodha.kite.TimeSequencer import get_n_previous_trading_days


def initialize_symbols_for_back_test(strategies, instruments_helper):
    for strategy in strategies:
        candle_intervals = set()

        for ind in strategy.get_indicators():
            candle_intervals.add(ind.get_candle_interval())

        for candle_interval in candle_intervals:
            if not initialize_symbol_for_back_test(strategy, candle_interval, instruments_helper):
                return False

    return True


def initialize_symbol_for_back_test(strategy, candle_interval, instruments_helper):
    data_manager = DataManagerFactory(strategy.get_kite_object(), strategy.get_mode()).get_object(
        period=strategy.get_period(),
        candle_interval=candle_interval,
        instruments_helper=instruments_helper
    )

    opening_time = strategy.get_opening_time()
    start_time = opening_time.replace(hour=9, minute=15, second=0, microsecond=0)
    end_time = opening_time.replace(hour=15, minute=30, second=0, microsecond=0)
    can_backtest_proceed = data_manager.put_data(strategy.get_symbol(), start_time, end_time)
    data_manager.close()

    # data_manager.put_data_to_csv(strategy.get_symbol(), start_time, end_time)
    return can_backtest_proceed


def start_threads_and_wait(threads):
    # Start all threads
    for t in threads:
        t.start()

    # Wait for all of them to finish
    for t in threads:
        t.join()


def back_test(kite, instruments_helper, opening_time):
    threads = []
    mode = BACK_TEST
    results = []
    orders = BackTestOrders(kite, 1, 0.90, EXCHANGE)

    # threads.extend(StrategyFactory(kite, mode, instruments_helper).get_strategies(PARABOLIC_SAR))
    # threads.extend(StrategyFactory(kite, mode, instruments_helper).get_strategies(SUPER_TREND_STRATEGY_7_3))
    # threads.extend(StrategyFactory(kite, mode, instruments_helper).get_strategies(ADX_STRATEGY))
    # threads.extend(StrategyFactory(kite, mode, instruments_helper).get_strategies(PARABOLIC_SAR_MTF))
    threads.extend(StrategyFactory(kite, mode, orders, instruments_helper, opening_time).get_strategies(SPM_STRATEGY))

    # Get all strategies
    strategies = []
    for worker in threads:
        if worker.strategy is not None:
            strategies.append(worker.strategy)

    if not initialize_symbols_for_back_test(strategies, instruments_helper):
        logging.warning("Back test cannot be done for opening time {}".format(opening_time))

        return [{
            'Status': "FAILED"
        }]

    start_threads_and_wait(threads)

    # We have to let the auto square off worker run in the last
    # Otherwise, it runs pretty fast, even before the strategy threads finish
    threads = [BackTestAutoSquareOffWorker(kite, orders=orders, opening_time=opening_time)]
    start_threads_and_wait(threads)

    for s in strategies:
        results.append(s.get_results())
        s.plot()

    return results


def back_test_range(kite, instruments_helper):
    start_time = datetime.datetime(2021, 12, 3, 9, 15, 0)
    days = 5
    opening_times = get_n_previous_trading_days(days, start_time)
    results = []

    for o in opening_times:
        result = back_test(kite, instruments_helper, o)
        if result[0]['Status'] == "PASS":
            results.extend(result)

    results_df = pd.DataFrame(results)
    print(results_df)
