import logging
import uuid
from math import floor

import pandas as pd

from trading.zerodha.kite.Orders import Orders


class BackTestOrders(Orders):
    """
    Wrapper class for mocking orders while doing a backtest.
    """

    def __init__(self, kite, leverage, order_pct, exchange):
        super().__init__(kite, leverage, order_pct, exchange)

        self.order_book = pd.DataFrame()
        self.all_positions = pd.DataFrame()
        self.active_positions = pd.DataFrame()

    def place_intraday_regular_market_order(self, candle_time, symbol, transaction_type, quantity, price):
        purchase_str = "{} {} quantities of scrip {}".format(transaction_type, quantity, symbol)

        self.order_book = self.order_book.append(
            pd.DataFrame([[transaction_type, quantity, price]],
                         columns=['action', 'quantity', 'price'], index=[candle_time]))

        if symbol in self.active_positions.index:
            # We already have an open position which could be long or short
            active_quantity = self.active_positions.loc[[symbol]]['quantity'][0]
            active_position = self.active_positions.loc[[symbol]]['action'][0]

            if active_position == "sell":
                new_quantity = (active_quantity * -1) + quantity
            elif active_position == "buy":
                new_quantity = active_quantity + (quantity * -1)
            else:
                raise ValueError("Active position should be buy or sell")

            if new_quantity == 0:
                # We have exited the position. Remove it from our records
                self.active_positions = self.active_positions.drop([symbol])

            ind = self.all_positions.index
            for i in range(len(self.all_positions)):
                if self.all_positions['tradingsymbol'][i] == symbol and self.all_positions['ExitPrice'][i] == -1:
                    self.all_positions.loc[ind[i], 'quantity'] = new_quantity

                    self.all_positions.loc[ind[i], 'ExitPrice'] = price
                    self.all_positions.loc[ind[i], 'ExitValue'] = price * self.all_positions['EntryQuantity'][i]
                    self.all_positions.loc[ind[i], 'ExitTime'] = candle_time

                    if self.all_positions['action'][i] == "sell":
                        self.all_positions.loc[ind[i], 'Net'] = \
                            (self.all_positions['EntryPrice'][i] - self.all_positions['ExitPrice'][i]) * \
                            self.all_positions['EntryQuantity'][i]
                    elif self.all_positions['action'][i] == "buy":
                        self.all_positions.loc[ind[i], 'Net'] = \
                            (self.all_positions['ExitPrice'][i] - self.all_positions['EntryPrice'][i]) * \
                            self.all_positions['EntryQuantity'][i]

        else:
            self.all_positions = self.all_positions.append(
                pd.DataFrame([[symbol, transaction_type, quantity, quantity, price, (quantity * price), -1, -1, -1, 0]],
                             columns=['tradingsymbol', 'action',
                                      'quantity',
                                      'EntryQuantity', 'EntryPrice', 'EntryValue',
                                      'ExitPrice', 'ExitValue', 'ExitTime',
                                      'Net'],
                             index=[candle_time])
            )
            self.active_positions = self.active_positions.append(
                pd.DataFrame([[quantity, transaction_type]], columns=['quantity', 'action'], index=[symbol]))

        logging.info(purchase_str)

        return str(uuid.uuid4())

    def place_mis_regular_sl_order(self, candle_time, symbol, transaction_type, quantity, sl_price):
        sl_price = floor(sl_price)
        purchase_str = "Setting {} stop loss for {} {} at current_price {}" \
            .format(transaction_type, quantity, symbol, sl_price)

        logging.info(purchase_str)

        return str(uuid.uuid4())

    def open_positions(self):
        df = self.all_positions.copy()
        if df.empty:
            logging.warning("No positions for the day")
            return pd.DataFrame(), pd.DataFrame()

        long_positions = df[df.quantity > 0]
        short_positions = df[df.quantity < 0]
        return long_positions, short_positions

    def open_orders(self):
        return list()

    def cancel_regular_order(self, order_id):
        pass

    def place_bracket_order(self, symbol, transaction_type, quantity, atr, price):
        return str(uuid.uuid4())

    def get_available_cash(self):
        return 10000.0

    def get_start_cash(self):
        return 10000.0
