import logging

from trading.errors.DataNotAvailableError import DataNotAvailableError
from trading.errors.NoCashError import NoCashError
from trading.workers.BackTestWorker import BackTestWorker


class BackTestStrategyRunner(BackTestWorker):
    def __init__(self, kite, strategy, **kwargs):
        super().__init__(kite, opening_time=strategy.get_opening_time(), **kwargs)

        self.strategy = strategy

    def do_run(self, candle_time):
        logging.debug(
            "Running strategy {} for symbol {}".format(self.strategy.__class__.__name__, self.strategy.symbol))

        try:
            for ind in self.strategy.get_indicators():
                try:
                    logging.debug(
                        "Running indicator {} for symbol {}".format(ind.__class__.__name__, self.strategy.symbol))
                    ind.calculate_lines(candle_time)
                except DataNotAvailableError:
                    pass

            self.strategy.act(candle_time)
        except (DataNotAvailableError, NoCashError):
            pass

    def stop(self, candle_time):
        for ind in self.strategy.get_indicators():
            ind.persist_indicator_values()
