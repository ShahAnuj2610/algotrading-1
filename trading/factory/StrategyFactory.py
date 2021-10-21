import datetime
from abc import ABC

from trading.constants import SUPER_TREND_STRATEGY_7_3, PARABOLIC_SAR, BACK_TEST, SETUP, STRATEGY_DB_PATH, LIVE, \
    EXCHANGE
from trading.factory.ParabolicSARStrategyFactory import ParabolicSARStrategyFactory
from trading.factory.SuperTrendStrategyFactory import SuperTrendStrategyFactory
from trading.zerodha.kite.BackTestOrders import BackTestOrders
from trading.zerodha.kite.Orders import Orders
from trading.zerodha.kite.TimeSequencer import get_previous_trading_day


class StrategyFactory(ABC):
    def __init__(self, kite, mode, instruments_helper):
        self.kite = kite
        self.mode = mode
        self.instruments_helper = instruments_helper
        self.leverage = 5
        self.order_pct = 0.50

    def get_strategies(self, name):
        if self.mode == BACK_TEST:
            orders = BackTestOrders(self.kite, self.leverage, self.order_pct, EXCHANGE)
            db_path = STRATEGY_DB_PATH + BACK_TEST.lower() + "/"

            # Choose your own date for back testing in different time period
            # Right now we only allow back testing for intra day trading
            opening_time = datetime.datetime(2021, 10, 19, 9, 15, 0)
        elif self.mode == SETUP:
            orders = BackTestOrders(self.kite, self.leverage, self.order_pct, EXCHANGE)
            db_path = STRATEGY_DB_PATH + LIVE.lower() + "/"

            opening_time = get_previous_trading_day()
            opening_time = opening_time.replace(hour=9, minute=15, second=0, microsecond=0)
        elif self.mode == LIVE:
            orders = Orders(self.kite, self.leverage, self.order_pct, EXCHANGE)
            db_path = STRATEGY_DB_PATH + LIVE.lower() + "/"
            opening_time = datetime.datetime.now()
        else:
            raise ValueError("Unknown mode {}".format(self.mode))

        if name == SUPER_TREND_STRATEGY_7_3:
            return SuperTrendStrategyFactory(self.kite, self.mode,
                                             instruments_helper=self.instruments_helper,
                                             orders=orders,
                                             db_path=db_path,
                                             opening_time=opening_time).get_strategies(name)
        elif name == PARABOLIC_SAR:
            return ParabolicSARStrategyFactory(self.kite, self.mode,
                                               instruments_helper=self.instruments_helper,
                                               orders=orders,
                                               db_path=db_path,
                                               opening_time=opening_time).get_strategies(name)
