import logging


class AutoSquareOff:
    def __init__(self, orders, kite):
        self.orders = orders
        self.kite = kite

    def close_open_positions(self, candle_time):
        """
        Close all open all_positions (long and short)
        If the open position is long, we issue a sell "market" order for the same quantity
        If the open position is short, we issue a buy "market" order for the same quantity
        """
        long_positions, short_positions = self.orders.open_positions()

        if not long_positions.empty:
            logging.info("Open long positions: {}".format(long_positions['tradingsymbol'].to_list()))

            for i in long_positions.index:
                self.orders.sell_intraday_regular_market_order_with_quantity(
                    candle_time, long_positions['tradingsymbol'][i], long_positions['quantity'][i], -1)

        if not short_positions.empty:
            logging.info("Open short positions: {}".format(short_positions['tradingsymbol'].to_list()))

            for i in short_positions.index:
                quantity = short_positions['quantity'][i]
                if quantity < 0:
                    # Short positions are represented by negative quantity
                    quantity = quantity * -1

                self.orders.buy_intraday_regular_market_order_with_quantity(
                    candle_time, short_positions['tradingsymbol'][i], quantity, -1)

        logging.info("Square off attempted")

    def cancel_open_regular_orders(self, candle_time):
        """
        Close open regular orders.
        This does not apply to bracket or cover orders
        Typically closes stop loss that are present in "TRIGGER PENDING" state
        """
        open_orders = self.orders.open_orders()

        if not open_orders:
            logging.info("No orders for the day")
            return

        logging.info("Open orders: {}", open_orders)

        for order_id in open_orders:
            self.orders.cancel_regular_order(order_id)

        logging.info("Square off for pending orders initiated")

    def square_off(self, candle_time):
        # The order of these executions are important
        # We first cancel any open orders. If it is done the other way round, then
        # it is possible we might cancel the orders which were issued to exit the all_positions
        self.cancel_open_regular_orders(candle_time)
        self.close_open_positions(candle_time)
