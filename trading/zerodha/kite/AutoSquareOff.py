import logging


class AutoSquareOff:
    def __init__(self, orders):
        self.orders = orders

    def close_open_positions(self):
        """
        Close all open positions (long and short)
        If the open position is long, we issue a sell "market" order for the same quantity
        If the open position is short, we issue a buy "market" order for the same quantity
        """
        long_positions, short_positions = self.orders.open_positions()

        if long_positions.empty or short_positions.empty:
            logging.info("No positions for the day")
            pass

        logging.info("Open long positions: {}", long_positions['tradingsymbol'].to_list())
        logging.info("Open short positions: {}", short_positions['tradingsymbol'].to_list())

        for i in long_positions.index:
            self.orders.sell_intraday_regular_market_order_with_quantity(long_positions['tradingsymbol'][i],
                                                                         long_positions['quantity'][i])

        for i in short_positions.index:
            self.orders.buy_intraday_regular_market_order_with_quantity(short_positions['tradingsymbol'][i],
                                                                        short_positions['quantity'][i])

        logging.info("Square off for open positions initiated")

    def cancel_open_regular_orders(self):
        """
        Close open regular orders.
        This does not apply to bracket or cover orders
        Typically closes stop loss that are present in "TRIGGER PENDING" state
        """
        open_orders = self.orders.open_orders()

        if not open_orders:
            logging.info("No orders for the day")
            pass

        logging.info("Open orders: {}", open_orders)

        for order_id in open_orders:
            self.orders.cancel_regular_order(order_id)

        logging.info("Square off for pending orders initiated")

    def square_off(self):
        # The order of these executions are important
        # We first cancel any open orders. If it is done the other way round, then
        # it is possible we might cancel the orders which were issued to exit the positions
        self.cancel_open_regular_orders()
        self.close_open_positions()
