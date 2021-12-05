import datetime
import logging

from trading.workers.BackTestWorker import BackTestWorker
from trading.zerodha.kite.AutoSquareOff import AutoSquareOff
from trading.zerodha.kite.BackTestOrders import BackTestOrders


class BackTestAutoSquareOffWorker(BackTestWorker):
    """
    Worker which automatically exits the all_positions when the cut off time is nearing.
    For equity class, the auto square off time imposed by Zerodha is 3.20PM after which a penalty is slapped
    for each open order. Hence we start to exit all_positions proactively

    NOTE: This work is specifically used for back testing only!!
    """
    def __init__(self, kite, **kwargs):
        super().__init__(kite, **kwargs)

        self.auto_square_off = AutoSquareOff(kwargs['orders'], kite)
        self.strategy = None

    def do_run(self, candle_time):
        current_hour = candle_time.hour
        current_minute = candle_time.minute

        if current_hour == 15 and current_minute > 24:
            logging.warning("Market close nearing. Current hour {} Current minute {}. "
                            "Squaring off all_positions".format(current_hour, current_minute))

            self.auto_square_off.square_off(candle_time)

    def stop(self, candle_time):
        pass
