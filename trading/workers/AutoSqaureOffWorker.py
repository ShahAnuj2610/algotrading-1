import logging

from trading.workers.LiveWorker import LiveWorker
from trading.zerodha.kite.AutoSquareOff import AutoSquareOff
from trading.zerodha.kite.Orders import Orders


class AutoSquareOffWorker(LiveWorker):
    """
    Worker which automatically exits the all_positions when the cut off time is nearing.
    For equity class, the auto square off time imposed by Zerodha is 3.20PM after which a penalty is slapped
    for each open order. Hence we start to exit all_positions proactively
    """
    def __init__(self, kite, **kwargs):
        super().__init__(kite, **kwargs)

        self.auto_square_off = AutoSquareOff(Orders(kite, None, None, None), kite)
        self.strategy = None

    def do_run(self, candle_time):
        current_hour = candle_time.hour
        current_minute = candle_time.minute

        if current_hour == 15 and current_minute > 15:
            logging.warning("Market close nearing. Current hour {} Current minute {}. "
                            "Squaring off all_positions".format(current_hour, current_minute))

            self.auto_square_off.square_off(candle_time)

    def stop(self, candle_time):
        pass
