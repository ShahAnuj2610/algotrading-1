import logging

from trading.errors.DataNotAvailableError import DataNotAvailableError
from trading.errors.NoCashError import NoCashError
from trading.workers.LiveWorker import LiveWorker


class LiveStrategyRunner(LiveWorker):
    def __init__(self, kite, strategy, **kwargs):
        super().__init__(kite, **kwargs)

        self.strategy = strategy

    def do_run(self, candle_time):
        t = candle_time
        allowed_start_time = t.replace(hour=9, minute=15, second=0, microsecond=0)

        t = candle_time
        allowed_end_time = t.replace(hour=15, minute=30, second=0, microsecond=0)

        if not (allowed_start_time <= candle_time <= allowed_end_time):
            logging.info("Candle time {} is not in the allowed live trading range".format(candle_time))
            return

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
