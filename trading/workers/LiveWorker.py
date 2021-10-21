import datetime
import logging
import time
from abc import ABC

from trading.workers.WorkerThread import WorkerThread


class LiveWorker(WorkerThread, ABC):
    """
    Worker thread for "live" use cases that runs every minute, exactly at the start of the minute.
    This is the core class which synchronizes the execution with the strike of the minute
    Every thread that runs part of this system should inherit the worker thread so that all executions are in sync
    The threads automatically exit after the market has ended
    """
    def __init__(self, kite, **kwargs):
        super().__init__(kite)

    def run(self):
        start_time = time.time()

        while True:
            candle_time = datetime.datetime.now().replace(microsecond=0)
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

            # Comment me for tests!
            self.sleep(start_time)
