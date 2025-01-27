from trading.constants import BACK_TEST, EXCHANGE, PARABOLIC_SAR, SETUP, ADAPTIVE_SAR_STRATEGY, PARABOLIC_SAR_MTF
from trading.data.DataManagerFactory import DataManagerFactory
from trading.factory.StrategyFactory import StrategyFactory
from trading.helpers.InstrumentsHelper import InstrumentsHelper


def initialize_symbols_for_back_test(strategies, instruments_helper):
    for strategy in strategies:
        candle_intervals = set()

        for ind in strategy.get_indicators():
            candle_intervals.add(ind.get_candle_interval())

        for candle_interval in candle_intervals:
            initialize_symbol_for_back_test(strategy, candle_interval, instruments_helper)


def initialize_symbol_for_back_test(strategy, candle_interval, instruments_helper):
    data_manager = DataManagerFactory(strategy.get_kite_object(), strategy.get_mode()).get_object(
        period=strategy.get_period(),
        candle_interval=candle_interval,
        instruments_helper=instruments_helper
    )

    opening_time = strategy.get_opening_time()
    start_time = opening_time.replace(hour=9, minute=15, second=0, microsecond=0)
    end_time = opening_time.replace(hour=15, minute=30, second=0, microsecond=0)
    data_manager.put_data(strategy.get_symbol(), start_time, end_time)
    data_manager.close()


def start_threads_and_wait(threads):
    # Start all threads
    for t in threads:
        t.start()

    # Wait for all of them to finish
    for t in threads:
        t.join()


def set_up(kite, instruments_helper):
    threads = []
    mode = SETUP

    # threads.extend(StrategyFactory(kite, mode, instruments_helper).get_strategies(PARABOLIC_SAR))
    # threads.extend(StrategyFactory(kite, mode, instruments_helper).get_strategies(SUPER_TREND_STRATEGY_7_3))
    # threads.extend(StrategyFactory(kite, mode, instruments_helper).get_strategies(ADAPTIVE_SAR_STRATEGY))
    threads.extend(StrategyFactory(kite, mode, orders, instruments_helper).get_strategies(PARABOLIC_SAR_MTF))

    # Get all strategies
    strategies = []
    for worker in threads:
        strategies.append(worker.strategy)

    initialize_symbols_for_back_test(strategies, instruments_helper)

    start_threads_and_wait(threads)
