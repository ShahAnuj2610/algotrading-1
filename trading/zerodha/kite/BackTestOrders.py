from math import floor
import logging
import uuid

from trading.zerodha.kite.Orders import Orders


class BackTestOrders(Orders):
    """
    Wrapper class for mocking orders while doing a backtest.
    """
    def __init__(self, kite, leverage, order_pct, exchange):
        super().__init__(kite, leverage, order_pct, exchange)

    def place_intraday_regular_market_order(self, symbol, transaction_type, quantity):
        purchase_str = "{} {} quantities of scrip {}".format(transaction_type, quantity, symbol)

        logging.info(purchase_str)

        return str(uuid.uuid4())

    def place_mis_regular_sl_order(self, symbol, transaction_type, quantity, sl_price):
        sl_price = floor(sl_price)
        purchase_str = "Setting {} stop loss for {} {} at price {}" \
            .format(transaction_type, quantity, symbol, sl_price)

        logging.info(purchase_str)

        return str(uuid.uuid4())

    def cancel_regular_order(self, order_id):
        pass

    def place_bracket_order(self, symbol, transaction_type, quantity, atr, price):
        return str(uuid.uuid4())

    def get_available_cash(self):
        return 10000.0
