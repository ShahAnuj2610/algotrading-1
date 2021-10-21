import threading
import time
from abc import ABC, abstractmethod


class WorkerThread(threading.Thread, ABC):
    def __init__(self, kite, **kwargs):
        super().__init__()
        self.kite = kite

    def run(self):
        raise RuntimeError("Please provide an implementation for the worker thread")

    @abstractmethod
    def do_run(self, candle_time):
        pass

    @abstractmethod
    def stop(self, candle_time):
        pass

    def sleep(self, start_time):
        time.sleep(60.0 - ((time.time() - start_time) % 60.0))
