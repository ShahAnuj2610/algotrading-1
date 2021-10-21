import logging
import time
from abc import ABC, abstractmethod

from trading.zerodha.kite.TimeSequencer import get_allowed_time_slots


class Strategy(ABC):
    def __init__(self, kite, symbol, indicators, **kwargs):
        self.kite = kite
        self.indicators = indicators

        self.symbol = str(symbol)

        self.mode = kwargs['mode']
        self.orders = kwargs['orders']
        self.opening_time = kwargs['opening_time']

        self.all_positions = []
        self.long_positions = []
        self.short_positions = []

        # Keeps track of how we are doing with the strategy
        # Strategies can occasionally check how good or bad it is doing
        # Can be used as a circuit breaker too
        self.net_income = 0.0

        # Allowed time slots at which the indicator can run
        # This depends on the candle interval. i.e 1 min, 2 min, etc
        self.allowed_time_slots = get_allowed_time_slots(self.get_period(), self.get_candle_interval())

    @abstractmethod
    def act(self, candle_time):
        pass

    def get_symbol(self):
        return self.symbol

    def get_period(self):
        return self.period

    def get_candle_length(self):
        return self.candle_length

    def get_candle_interval(self):
        return self.candle_interval

    def get_kite_object(self):
        return self.kite

    def get_db_path(self):
        return self.db_path

    def get_opening_time(self):
        return self.opening_time

    def get_mode(self):
        """
        Determines whether it is back test or not
        :return:
        """
        return self.mode

    def can_order(self, candle_time):
        current_hour = candle_time.hour
        current_minute = candle_time.minute

        if current_hour == 15 and current_minute > 10:
            logging.warning("Market close nearing. Current hour {} Current minute {}. "
                            "Not taking any new positions {}"
                            .format(current_hour, current_minute, self.__class__.__name__))
            return False

        return True

    def enter_long_position(self, candle_time, price, stoploss_price):
        if not self.can_order(candle_time):
            return

        if len(self.long_positions) != 0:
            raise ValueError("Entering long position for symbol {} at {} when we are already long??".format(
                self.symbol, candle_time
            ))

        if len(self.short_positions) > 1:
            raise ValueError("Too many short positions ({}) present. Which one to close?".format(
                len(self.short_positions))
            )

        if len(self.short_positions) == 1:
            logging.info("Exiting short position for symbol {} at {}".format(self.symbol, candle_time))

            short_position = self.short_positions[0]
            quantity = short_position['quantity']

            self.orders.buy_intraday_regular_market_order_with_quantity(self.symbol, quantity)
            # stoploss_order_id = short_position['stoploss_order_id']
            # self.orders.cancel_regular_order(stoploss_order_id)
            self.short_positions.clear()

            # Pausing for margins to get reflected
            time.sleep(5)

        logging.info("Entering new long position for symbol {} at {}".format(self.symbol, candle_time))

        order_id, quantity = \
            self.orders.buy_intraday_regular_market_order(self.symbol, price)

        self.long_positions.append({
            "quantity": quantity,
            "order_id": order_id,
            "candle_time": candle_time
        })

    def enter_short_position(self, candle_time, price, stoploss_price):
        if not self.can_order(candle_time):
            return

        if len(self.short_positions) > 0:
            raise ValueError("Entering short position for symbol {} at {} when we are already short??".format(
                self.symbol, candle_time
            ))

        if len(self.long_positions) > 1:
            raise ValueError("Too many long positions ({}) present. Which one to close?".format(
                len(self.long_positions))
            )

        if len(self.long_positions) == 1:
            logging.info("Exiting long position for symbol {} at {}".format(self.symbol, candle_time))

            long_position = self.long_positions[0]
            quantity = long_position['quantity']

            self.orders.sell_intraday_regular_market_order_with_quantity(self.symbol, quantity)
            # stoploss_order_id = long_position['stoploss_order_id']
            # self.orders.cancel_regular_order(stoploss_order_id)
            self.long_positions.clear()

            # Pausing for margins to get reflected
            time.sleep(5)

        logging.info("Entering new short position for symbol {} at {}".format(self.symbol, candle_time))

        order_id, quantity = \
            self.orders.sell_intraday_regular_market_order(self.symbol, price)

        self.short_positions.append({
            "quantity": quantity,
            "order_id": order_id,
            "candle_time": candle_time
        })

    def get_indicators(self):
        return self.indicators
