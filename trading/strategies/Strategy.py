import logging
from abc import ABC, abstractmethod

from trading.zerodha.kite.Orders import Orders
from trading.zerodha.kite.Period import Period


class Strategy(ABC):
    def __init__(self, kite, indicators, **kwargs):
        self.kite = kite
        self.indicators = indicators

        self.exchange = kwargs['exchange']
        self.symbol = kwargs['symbol']

        self.period = Period.MIN
        self.candle_length = 7
        self.candle_interval = 1
        self.leverage = 5
        self.order_pct = 0.50

        self.orders = Orders(self.kite, self.leverage, self.order_pct, self.exchange)
        self.all_positions = []
        self.long_positions = []
        self.short_positions = []

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
            pass

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

        logging.info("Entering new long position for symbol {} at {}".format(self.symbol, candle_time))

        order_id, stoploss_order_id, quantity = \
            self.orders.buy_intraday_regular_market_order(self.symbol, price)

        self.long_positions.append({
            "quantity": quantity,
            "order_id": order_id,
            "candle_time": candle_time
        })

        print(self.long_positions)

    def enter_short_position(self, candle_time, price, stoploss_price):
        if not self.can_order(candle_time):
            pass

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

        logging.info("Entering new short position for symbol {} at {}".format(self.symbol, candle_time))

        order_id, stoploss_order_id, quantity = \
            self.orders.sell_intraday_regular_market_order(self.symbol, price)

        self.short_positions.append({
            "quantity": quantity,
            "order_id": order_id,
            "candle_time": candle_time
        })

    def get_indicators(self):
        return self.indicators
