import logging
import sqlite3
import sys
import traceback
from abc import ABC, abstractmethod

from trading.constants import EXCHANGE, TICKS_DB_PATH
from trading.zerodha.kite.Orders import Orders
from trading.zerodha.kite.Period import Period


class Strategy(ABC):
    def __init__(self, kite, symbol, indicators, **kwargs):
        self.kite = kite
        self.indicators = indicators

        self.exchange = EXCHANGE
        self.symbol = str(symbol)

        self.period = Period.MIN
        self.candle_length = 7
        self.candle_interval = 1
        self.leverage = 5
        self.order_pct = 0.50

        self.orders = Orders(self.kite, self.leverage, self.order_pct, self.exchange)
        self.all_positions = []
        self.long_positions = []
        self.short_positions = []

        # Prepare the ticks database to receive ticks for this symbol
        self.create_symbols_ticks_table()

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

    def create_symbols_ticks_table(self):
        db = sqlite3.connect(TICKS_DB_PATH)

        c = db.cursor()
        table_name = self.symbol  # + "-" + str(self.suffix)
        c.execute(
            "CREATE TABLE IF NOT EXISTS {} (ts datetime primary key, price real(15,5), volume integer)".format(
                table_name))
        try:
            db.commit()
        except Exception as e:
            print(e)
            print(traceback.format_exc())
            sys.exit(1)

        db.close()

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
