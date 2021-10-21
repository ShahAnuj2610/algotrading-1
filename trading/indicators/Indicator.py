import logging
from abc import ABC, abstractmethod

import pandas as pd
from sqlalchemy import create_engine

from trading.data.DataManagerFactory import DataManagerFactory
from trading.errors.DataNotAvailableError import DataNotAvailableError
from trading.zerodha.kite.TimeSequencer import get_previous_time, get_time_sequence


class Indicator(ABC):
    def __init__(self, indicator_name, strategy, **kwargs):
        if not strategy:
            raise ValueError("Strategy is not initialised for indicator {}".format(indicator_name))

        self.indicator_name = indicator_name
        self.strategy = strategy

        self.symbol = strategy.get_symbol()
        self.period = strategy.get_period()
        self.candle_length = strategy.get_candle_length()
        self.candle_interval = strategy.get_candle_interval()

        self.mode = strategy.get_mode()
        self.kite = strategy.get_kite_object()
        self.instruments_helper = kwargs['instruments_helper']

        self.indicator_db_path = strategy.get_db_path() + self.strategy.__class__.__name__ + "_" + str(self.candle_interval) \
                                 + "_" + str(self.period.name) + ".db"
        self.indicator_table_name = self.symbol + "_" + self.indicator_name

        # Historical dataframe
        self.values = self.load_indicator_values()

    def calculate_lines(self, candle_time):
        self.do_calculate_lines(candle_time)

    @abstractmethod
    def do_calculate_lines(self, candle_time):
        pass

    def get_previous_indicator_time(self, candle_time):
        return get_previous_time(self.period, self.candle_interval, candle_time)

    def get_lines(self, n, candle_time):
        candle_sequence = self.get_n_candle_sequence(n, candle_time)
        df = self.values.tail(n)
        self.validate_candles(df, reversed(candle_sequence))
        return df.copy()

    def store_indicator_value(self, df, candle_time):
        self.validate_candles_and_throw(df, [self.get_previous_indicator_time(candle_time)])
        self.values = self.values.append(df)

    def get_data(self, candle_end_time):
        candle_sequence = self.get_candle_sequence(candle_end_time)
        candle_start_time = candle_sequence[-1]

        df = self.do_get_data(candle_start_time, candle_end_time)

        self.validate_candles(df, reversed(candle_sequence))

        return df.copy()

    def get_data_for_time(self, candle_end_time):
        candle_start_time = get_previous_time(self.period, self.candle_interval, candle_end_time)

        df = self.do_get_data(candle_start_time, candle_end_time)

        self.validate_candles(df, [candle_start_time])

        return df.copy()

    def do_get_data(self, start_time, end_time):
        data_fetcher = DataManagerFactory(self.kite, self.mode).\
            get_object(period=self.period,
                       candle_interval=self.candle_interval,
                       instruments_helper=self.instruments_helper)
        df = data_fetcher.get_data(self.symbol, start_time, end_time)
        data_fetcher.close()

        return df

    def get_candle_sequence(self, candle_end_time):
        return get_time_sequence(self.period, self.candle_interval, self.candle_length, candle_end_time)

    def get_n_candle_sequence(self, n, candle_end_time):
        return get_time_sequence(self.period, self.candle_interval, n, candle_end_time)

    def get_actual_and_expected_candles(self, actual_candles_in, expected_candles):
        actual_candles = []
        for i in range(len(actual_candles_in)):
            actual_candles.append(str(actual_candles_in.index[i]))

        expected_candles = [str(i) for i in expected_candles]

        return actual_candles, expected_candles

    def persist_indicator_values(self):
        """
        Store indicator values to database for reference in the next trading day
        Without storing indicator values, every day's first few minutes of trading
        is wasted in priming the indicator. Instead if we memorise the indicator values,
        then it becomes incredibly easy to start trading in the beginning of the day
        which is when the market moves
        """
        engine = create_engine(f"sqlite:///" + self.indicator_db_path)
        # For now pick the last 50 entries
        df = self.values.tail(50)
        df.index = df.index.strftime('%Y-%m-%d %H:%M:%S')
        df.to_sql(self.indicator_table_name, engine, if_exists='replace', index=True)
        engine.dispose()

    def load_indicator_values(self):
        """
        Load the indicator values that were stored when the program ended
        By doing this load, we quickly regain context and do not have to
        build indicators from first in the start of trading day
        :return: dataframe containing the indicator values
        """
        engine = create_engine(f"sqlite:///" + self.indicator_db_path)
        try:
            cnx = engine.connect()
            df = pd.read_sql_table(self.indicator_table_name, cnx)
            df = df.set_index('ts')
            df.index = pd.to_datetime(df.index)
            return df.copy()
        except ValueError:
            logging.warning("Table {} does not exist. Starting afresh".format(self.indicator_table_name))
            return pd.DataFrame()
        finally:
            engine.dispose()

    def get_previous_indicator_value(self, candle_time):
        """
        Return the indicator value at the previous candle time
        We do computations in a stream manner and hence previous indicator value
        is required for a continuous computation
        :param candle_time: The time at which the function is called
        :return: the previous value if present and if expected, else an empty dataframe
        """
        if self.values.empty:
            return pd.DataFrame()

        expected_time = str(self.get_n_candle_sequence(2, candle_time)[-1])
        actual_time = str(self.values.tail(1).index[0])

        if expected_time != actual_time:
            logging.error("Database state is not in sync with program! Expected time: {}, Actual time {}".format(
                expected_time, actual_time
            ))
            logging.info("Assuming a fresh run")
            return pd.DataFrame()

        return self.values.tail(1)

    def validate_candles(self, actual_candles_in, expected_candles):
        actual_candles, expected_candles = self.get_actual_and_expected_candles(actual_candles_in, expected_candles)

        if actual_candles != expected_candles:
            logging.debug("Expected candles: {} for indicator: {}".format(expected_candles, self.indicator_name))
            logging.debug("Actual candles: {} for indicator: {}".format(str(actual_candles), self.indicator_name))

            raise DataNotAvailableError("Data not available")

    def validate_candles_and_throw(self, actual_candles_in, expected_candles):
        actual_candles, expected_candles = self.get_actual_and_expected_candles(actual_candles_in, expected_candles)

        if actual_candles != expected_candles:
            logging.info("Expected candles: {} for indicator: {}".format(expected_candles, self.indicator_name))
            logging.info("Actual candles: {} for indicator: {}".format(str(actual_candles), self.indicator_name))

            raise ValueError("Candles mismatch")
