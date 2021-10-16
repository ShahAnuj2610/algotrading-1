import datetime
import logging
import threading
import time
from abc import ABC, abstractmethod


class WorkerThread(threading.Thread, ABC):
    """
    Worker thread that runs every minute, exactly at the start of the minute.
    This is the core class which synchronizes the execution with the strike of the minute
    Every thread that runs part of this system should inherit the worker thread so that all executions are in sync
    The threads automatically exit after the market has ended
    """
    def __init__(self, kite, **kwargs):
        super().__init__()
        logging.basicConfig(format='%(asctime)s :: %(levelname)s :: %(message)s', level=logging.INFO)
        self.kite = kite

    def run(self):
        # Uncomment me for test!
        candle_time = datetime.datetime(2021, 10, 11, 14, 31, 0)

        start_time = time.time()

        while True:
            # Comment me for tests!
            # candle_time = datetime.datetime.now().replace(microsecond=0)
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
            # self.sleep(start_time)

            # Uncomment me for tests!
            candle_time = candle_time + datetime.timedelta(minutes=1)

    @abstractmethod
    def do_run(self, candle_time):
        pass

    @abstractmethod
    def stop(self, candle_time):
        pass

    def sleep(self, start_time):
        time.sleep(60.0 - ((time.time() - start_time) % 60.0))
