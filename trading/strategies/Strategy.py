import logging
import time
from abc import ABC, abstractmethod

from trading.zerodha.kite.Period import Period
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

        interval = 1000
        period = Period.MIN
        for i in self.indicators:
            if i.candle_interval < interval:
                interval = i.candle_interval

            if i.period != period:
                raise ValueError("Only minute processing is supported for now")

        # Allowed time slots at which the strategy can run
        # When strategy looks at only one time frame, this should not be an issue
        # However, if the strategy looks at multiple time frames, then the indicator with lowest time frame matters
        # The strategy should be aware that it will be run on the indicator with lowest time frame
        self.allowed_time_slots = get_allowed_time_slots(period, interval)

    def act(self, candle_time):
        if not candle_time.strftime('%H:%M') in self.allowed_time_slots:
            return

        self.do_act(candle_time)

    @abstractmethod
    def do_act(self, candle_time):
        pass

    def plot(self):
        pass

    def get_symbol(self):
        return self.symbol

    def get_period(self):
        return self.period

    def get_candle_length(self):
        return self.candle_length

    def get_indicators(self):
        return self.indicators

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
                            "Not taking any new all_positions {}"
                            .format(current_hour, current_minute, self.__class__.__name__))
            return False

        return True

    def stop_and_reverse_enter_long_position(self, candle_time, price):
        """
        Enter a new long position by exiting the previous short position
        This method has to be used only when we want 1 open position for the liftime of a strategy
        If we want multiple open long all_positions, then call enter_long_position method directly

        :param candle_time: Time at which we enter a new position
        :param price: Price at which we enter a new position
        :return: None. But adds the new short position to the list of open short all_positions whose length should be ideally 1
        """

        if not self.can_order(candle_time):
            return

        if len(self.long_positions) != 0:
            raise ValueError("Entering long position for symbol {} at {} when we are already long??".format(
                self.symbol, candle_time
            ))

        if len(self.short_positions) > 1:
            raise ValueError("Too many short all_positions ({}) present. Which one to close?".format(
                len(self.short_positions))
            )

        if len(self.short_positions) == 1:
            self.exit_short_position(candle_time, price)

        self.long_positions.append(self.enter_long_position(price, candle_time))

    def stop_and_reverse_enter_short_position(self, candle_time, price):
        """
        Enter a new short position by exiting the previous long position
        This method has to be used only when we want 1 open position at the liftime of
        a strategy
        If we want multiple open short all_positions, then call enter_short_position method directly

        :param candle_time: Time at which we enter a new position
        :param price: Price at which we enter a new position
        :return: None. But adds the new short position to the list of open short all_positions whose length should be ideally 1
        """
        if not self.can_order(candle_time):
            return

        if len(self.short_positions) > 0:
            raise ValueError("Entering short position for symbol {} at {} when we are already short??".format(
                self.symbol, candle_time
            ))

        if len(self.long_positions) > 1:
            raise ValueError("Too many long all_positions ({}) present. Which one to close?".format(
                len(self.long_positions))
            )

        if len(self.long_positions) == 1:
            self.exit_long_position(candle_time, price)

        self.short_positions.append(self.enter_short_position(price, candle_time))

    def enter_long_position(self, price, candle_time, stoploss_price=0):
        """
        Enter a new long position
        This method should be called only when we want multiple open all_positions to coexist

        :param price: Price at which we enter the new position
        :param candle_time: Candle time at which we enter the new position
        :param stoploss_price: Price at which the position should be exited
        :return: Position details as dictionary
        """
        logging.info("Entering new long position for symbol {} at {}".format(self.symbol, candle_time))

        order_id, quantity = \
            self.orders.buy_intraday_regular_market_order(candle_time, self.symbol, price)

        return {
            "quantity": quantity,
            "entry_price": price,
            "order_id": order_id,
            "stoploss_price": stoploss_price,
            "candle_time": candle_time
        }

    def enter_short_position(self, price, candle_time, stoploss_price=0):
        """
        Enter a new short position
        This method should be called only when we want multiple open all_positions to coexist

        :param price: Price at which we enter the new position
        :param candle_time: Candle time at which we enter the new position
        :param stoploss_price: Price at which the position should be exited
        :return: Position details as dictionary
        """
        logging.info("Entering new short position for symbol {} at {}".format(self.symbol, candle_time))

        order_id, quantity = \
            self.orders.sell_intraday_regular_market_order(candle_time, self.symbol, price)

        return {
            "quantity": quantity,
            "entry_price": price,
            "order_id": order_id,
            "stoploss_price": stoploss_price,
            "candle_time": candle_time
        }

    def exit_long_position(self, candle_time, current_price):
        if len(self.long_positions) == 0:
            logging.warning("There are no long all_positions to exit")
            return

        logging.info("Exiting long position for symbol {} at {}".format(self.symbol, candle_time))

        long_position = self.long_positions[0]
        quantity = long_position['quantity']

        self.orders.sell_intraday_regular_market_order_with_quantity(candle_time, self.symbol, quantity, current_price)
        # stoploss_order_id = long_position['stoploss_order_id']
        # self.orders.cancel_regular_order(stoploss_order_id)
        self.long_positions.clear()

    def exit_short_position(self, candle_time, current_price):
        if len(self.short_positions) == 0:
            logging.warning("There are no short all_positions to exit")
            return

        logging.info("Exiting short position for symbol {} at {}".format(self.symbol, candle_time))

        short_position = self.short_positions[0]
        quantity = short_position['quantity']

        self.orders.buy_intraday_regular_market_order_with_quantity(candle_time, self.symbol, quantity, current_price)
        # stoploss_order_id = short_position['stoploss_order_id']
        # self.orders.cancel_regular_order(stoploss_order_id)
        self.short_positions.clear()

    def get_results(self):
        """
        Calculate various statistics for this strategy. Typically the following are returned
        - Net profit
        - Net loss
        - Total trades
        - Total winning trades
        - Total loosing trades
        - Win %
        - Loss %
        - Max winning streak
        - Max loosing streak
        :return: A dictionary containing the above statistics
        """
        # Since auto sqaure off worker does not know the current price at which the square off is triggered
        # we manually hack the value in
        some_indicator = self.indicators[0]
        some_indicator_values = some_indicator.get_all_values()

        ind = self.orders.order_book.index

        if len(ind) == 0:
            return

        auto_square_off_value = some_indicator_values['close'].iloc[-1]
        self.orders.order_book.loc[ind[-1], 'price'] = auto_square_off_value

        ind = self.orders.all_positions.index
        self.orders.all_positions.loc[ind[-1], 'ExitPrice'] = auto_square_off_value
        self.orders.all_positions.loc[ind[-1], 'ExitValue'] = auto_square_off_value * \
                                                              self.orders.all_positions['EntryQuantity'][-1]

        if self.orders.all_positions['action'].iloc[-1] == "sell":
            self.orders.all_positions.loc[ind[-1], 'Net'] = \
                (self.orders.all_positions['EntryPrice'][-1] - self.orders.all_positions['ExitPrice'][-1]) * \
                self.orders.all_positions['EntryQuantity'][-1]
        elif self.orders.all_positions['action'].iloc[-1] == "buy":
            self.orders.all_positions.loc[ind[-1], 'Net'] = \
                (self.orders.all_positions['ExitPrice'][-1] - self.orders.all_positions['EntryPrice'][-1]) * \
                self.orders.all_positions['EntryQuantity'][-1]

        #print(self.orders.order_book)
        #print(self.orders.all_positions)
        #print(self.orders.active_positions)

        if len(self.orders.active_positions) != 0:
            raise ValueError("We have not closed open positions!!")

        return {
            'Status': "PASS",
            'Total Orders': len(self.orders.order_book),
            'Total Trades': len(self.orders.all_positions),
            'Total Cash Invested': self.orders.get_start_cash(),
            'Net income': self.orders.all_positions['Net'].sum(),
            'ROI': (self.orders.all_positions['Net'].sum() / self.orders.get_start_cash()) * 100,
            'Total Winning Trades': len(self.orders.all_positions[self.orders.all_positions.Net > 0]),
            'Total Loosing Trades': len(self.orders.all_positions[self.orders.all_positions.Net < 0])
        }
