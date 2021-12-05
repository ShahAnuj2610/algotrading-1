import logging
import time
from math import floor

import pandas as pd

from trading.errors.NoCashError import NoCashError
from trading.zerodha.kite.Retry import retry


class Orders:
    """
    Wrapper class for placing orders with Zerodha.
    It requires
    - A valid kite object, that has been authenticated with zerodha
    - The amount of leverage offered. Currently, it is assumed to be 5. i.e 20% margin offered by the broker
    - An order percentage - Safety net guarding the amount of cash that can be deployed
    - The exchange in which the transaction should take place (i.e NSE or BSE)
    """

    def __init__(self, kite, leverage, order_pct, exchange):
        logging.basicConfig(format='%(asctime)s :: %(levelname)s :: %(message)s', level=logging.INFO)
        self.kite = kite
        self.leverage = leverage
        self.order_pct = order_pct
        self.exchange = exchange

    def buy_intraday_regular_market_order(self, candle_time, symbol, current_price):
        """
        Places a market buy order for symbol with product type MIS
        Exert caution while calling this method since it does NOT place any stop loss order
        :param candle_time: The time at which the transaction is being made
        :param symbol: The scrip
        :param current_price: Current current_price of the scrip. This is used to automatically calculate number of units (i.e quantity)
        :return: a pair of order_id and the number of units transacted
        """
        quantity = self.get_quantity(symbol, current_price)
        order_id = self.place_intraday_regular_market_order(candle_time, symbol, "buy", quantity, current_price)

        return order_id, quantity

    def buy_intraday_regular_market_order_with_quantity(self, candle_time, symbol, quantity, current_price):
        """
        Places a market buy order for symbol with product type MIS
        Exert caution while calling this method since it does NOT place any stop loss order
        :param candle_time: The time at which the transaction is being made
        :param symbol: The scrip
        :param quantity: Number of units to transact
        :param current_price: The current current_price
        :return: order_id for the executed order
        """
        return self.place_intraday_regular_market_order(candle_time, symbol, "buy", quantity, current_price)

    def buy_intraday_regular_market_order_with_stop_loss(self, candle_time, symbol, current_price, stoploss_price):
        """
        Places a market buy order for symbol with product type MIS along with a sell stop loss at stoploss_price
        :param candle_time: The time at which the transaction is being made
        :param symbol: The scrip
        :param current_price: Current current_price of the scrip. This is used to automatically calculate number of
        units (i.e quantity) :param stoploss_price: Stop loss current_price for the scrip
        :param stoploss_price: Sell stoploss current_price
        :return: a tuple of order_id,
        the number of units transacted and the stop loss order id which can be cancelled later
        """
        quantity = self.get_quantity(symbol, current_price)
        order_id = self.place_intraday_regular_market_order(candle_time, symbol, "buy", quantity, current_price)
        stoploss_order_id = self.place_mis_regular_sl_order(candle_time, symbol, "sell", quantity, stoploss_price)

        return order_id, stoploss_order_id, quantity

    def sell_intraday_regular_market_order(self, candle_time, symbol, current_price):
        """
        Places a market sell order for symbol with product type MIS
        Exert caution while calling this method since it does NOT place any stop loss order
        :param candle_time: The time at which the transaction is being made
        :param symbol: The scrip
        :param current_price: Current current_price of the scrip. This is used to automatically calculate number of units (i.e quantity)
        :return: a pair of order_id and the number of units transacted
        """
        quantity = self.get_quantity(symbol, current_price)
        order_id = self.place_intraday_regular_market_order(candle_time, symbol, "sell", quantity, current_price)

        return order_id, quantity

    def sell_intraday_regular_market_order_with_quantity(self, candle_time, symbol, quantity, current_price):
        """
        Places a market sell order for symbol with product type MIS
        Exert caution while calling this method since it does NOT place any stop loss order
        :param candle_time: The time at which the transaction is being made
        :param symbol: The scrip
        :param quantity: Number of units to transact
        :param current_price: The current current_price
        :return: order_id for the executed order
        """
        return self.place_intraday_regular_market_order(candle_time, symbol, "sell", quantity, current_price)

    def sell_intraday_regular_market_order_with_stop_loss(self, candle_time, symbol, current_price, stoploss_price):
        """
        Places a market sell order for symbol with product type MIS along with a buy stop loss at stoploss_price
        :param candle_time: The time at which the transaction is being made
        :param symbol: The scrip
        :param current_price: Current current_price of the scrip. This is used to automatically calculate number of
        units (i.e quantity) :param stoploss_price: Stop loss current_price for the scrip
        :param stoploss_price: Buy stoploss current_price
        :return: a tuple of order_id,
        the number of units transacted and the stop loss order id which can be cancelled later
        """
        quantity = self.get_quantity(symbol, current_price)
        order_id = self.place_intraday_regular_market_order(candle_time, symbol, "sell", quantity, current_price)
        stoploss_order_id = self.place_mis_regular_sl_order(candle_time, symbol, "buy", quantity, stoploss_price)

        return order_id, stoploss_order_id, quantity

    def get_quantity(self, symbol, current_price):
        """
        Calculates the number of units for a transaction. This serves as a default for strategies that are
        not very specific about calculating the number of units
        In the default case, we find the amount of hard cash available (i.e inclusive of margins blocked)
        and find the total margin we have with the available cash using the leverage provided to us by the broker.
        As a measure of safety, we deploy only a percentage of the cash which is the disposable margin
        We finally use this disposable margin to find the number of units
        :param symbol: The scrip
        :param current_price: Current current_price of the scrip
        :return: Number of units that can be transacted
        """
        cash_available = self.get_available_cash()
        total_margin = cash_available * self.leverage
        disposable_margin = total_margin * self.order_pct
        quantity = floor(disposable_margin / current_price)

        if quantity <= 0:
            # If we cannot even buy one stock, then throw
            # Strategies should not fail on receiving this error. They are expected to retry
            raise NoCashError(
                "Stock {} is too expensive. Margin available {}, Cash available {}, Cash needed {}, current current_price {}, "
                    .format(symbol, disposable_margin, cash_available, current_price - disposable_margin,
                            current_price))

        return quantity

    @retry(tries=5, delay=2, backoff=2)
    def open_positions(self):
        df = pd.DataFrame(self.kite.all_positions()["day"])
        if df.empty:
            logging.warning("No all_positions for the day")
            return pd.DataFrame(), pd.DataFrame()

        long_positions = df[df.quantity > 0]
        short_positions = df[df.quantity < 0]
        return long_positions, short_positions

    @retry(tries=5, delay=2, backoff=2)
    def open_orders(self):
        ord_df = pd.DataFrame(self.kite.orders())

        if ord_df.empty:
            return list()

        return ord_df[ord_df['status'].isin(["TRIGGER PENDING", "OPEN"])]["order_id"].tolist()

    @retry(tries=5, delay=2, backoff=2)
    def place_intraday_regular_market_order(self, candle_time, symbol, transaction_type, quantity, price):
        purchase_str = "{} {} quantities of scrip {}".format(transaction_type, quantity, symbol)

        logging.info(purchase_str)

        transaction_type = self.get_transaction_type(transaction_type)

        order = self.kite.place_order(tradingsymbol=symbol,
                                      exchange=self.exchange,
                                      transaction_type=transaction_type,
                                      quantity=quantity,
                                      order_type=self.kite.ORDER_TYPE_MARKET,
                                      product=self.kite.PRODUCT_MIS,
                                      variety=self.kite.VARIETY_REGULAR)

        # Pausing for margins to get reflected
        time.sleep(5)

        return order

    @retry(tries=5, delay=2, backoff=2)
    def place_mis_regular_sl_order(self, candle_time, symbol, transaction_type, quantity, sl_price):
        sl_price = floor(sl_price)
        purchase_str = "Setting {} stop loss for {} {} at current_price {}" \
            .format(transaction_type, quantity, symbol, sl_price)

        logging.info(purchase_str)

        transaction_type = self.get_transaction_type(transaction_type)

        return self.kite.place_order(tradingsymbol=symbol,
                                     exchange=self.exchange,
                                     transaction_type=transaction_type,
                                     quantity=quantity,
                                     order_type=self.kite.ORDER_TYPE_SLM,
                                     price=sl_price,
                                     trigger_price=sl_price,
                                     product=self.kite.PRODUCT_MIS,
                                     variety=self.kite.VARIETY_REGULAR)

    @retry(tries=5, delay=2, backoff=2)
    def cancel_regular_order(self, order_id):
        self.kite.cancel_order(variety=self.kite.VARIETY_REGULAR, order_id=order_id)

    @retry(tries=5, delay=2, backoff=2)
    def place_bracket_order(self, symbol, transaction_type, quantity, atr, price):
        transaction_type = self.get_transaction_type(transaction_type)

        self.kite.place_order(tradingsymbol=symbol,
                              exchange=self.exchange,
                              transaction_type=transaction_type,
                              quantity=quantity,
                              order_type=self.kite.ORDER_TYPE_LIMIT,
                              price=price,  # BO has to be a limit order, set a low current_price threshold
                              product=self.kite.PRODUCT_MIS,
                              variety=self.kite.VARIETY_BO,
                              squareoff=int(6 * atr),
                              stoploss=int(3 * atr),
                              trailing_stoploss=2)

    @retry(tries=5, delay=2, backoff=2)
    def get_available_cash(self):
        return self.kite.margins()['equity']['available']['live_balance']

    def get_transaction_type(self, transaction_type):
        if transaction_type == "buy":
            return self.kite.TRANSACTION_TYPE_BUY
        elif transaction_type == "sell":
            return self.kite.TRANSACTION_TYPE_SELL
        else:
            raise ValueError("Unknown transaction type {}".format(transaction_type))
