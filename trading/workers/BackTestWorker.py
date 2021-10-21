import datetime
import logging
from abc import ABC

from trading.workers.WorkerThread import WorkerThread


class BackTestWorker(WorkerThread, ABC):
    def __init__(self, kite, **kwargs):
        super().__init__(kite)

        self.opening_time = kwargs['opening_time']

    def run(self):
        candle_time = self.opening_time

        while True:
            current_hour = candle_time.hour
            current_minute = candle_time.minute

            if current_hour == 15 and current_minute > 30:
                logging.info("Market has ended. Current hour {} Current minute {}. "
                             "Exiting thread and recording state".format(current_hour, current_minute))
                self.stop(candle_time)
                break

            # Reset the second to 0. We are only concerned about the minute
            # There could a few milliseconds or probably 1 or 2 seconds difference
            # For our use case it is okay
            self.do_run(candle_time.replace(second=0))

            candle_time = candle_time + datetime.timedelta(minutes=1)

