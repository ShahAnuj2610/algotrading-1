import datetime
from abc import ABC

from trading.constants import SUPER_TREND_STRATEGY_7_3, PARABOLIC_SAR, BACK_TEST, SETUP, STRATEGY_DB_PATH, LIVE, \
    EXCHANGE, ADAPTIVE_SAR_STRATEGY, ADX_STRATEGY, PARABOLIC_SAR_MTF, SPM_STRATEGY
from trading.factory.ADXStrategyFactory import ADXStrategyFactory
from trading.factory.ParabolicSARMTFStrategyFactory import ParabolicSARMTFStrategyFactory
from trading.factory.ParabolicSARStrategyFactory import ParabolicSARStrategyFactory
from trading.factory.StructuralPivotMethodStrategyFactory import StructuralPivotMethodStrategyFactory
from trading.factory.SuperTrendStrategyFactory import SuperTrendStrategyFactory
from trading.factory.AdaptiveSARStrategyFactory import AdaptiveSARStrategyFactory
from trading.zerodha.kite.BackTestOrders import BackTestOrders
from trading.zerodha.kite.Orders import Orders
from trading.zerodha.kite.TimeSequencer import get_previous_trading_day


class StrategyFactory(ABC):
    def __init__(self, kite, mode, orders, instruments_helper, opening_time):
        self.kite = kite
        self.mode = mode
        self.orders = orders
        self.instruments_helper = instruments_helper
        self.leverage = 5
        self.order_pct = 0.50
        self.opening_time = opening_time.replace(hour=9, minute=15, second=0, microsecond=0)

    def get_strategies(self, name):
        if self.mode == BACK_TEST:
            db_path = STRATEGY_DB_PATH + BACK_TEST.lower() + "/"
            # Choose your own date for back testing in different time period
            # Right now we only allow back testing for intra day trading
            opening_time = self.opening_time
        elif self.mode == SETUP:
            orders = BackTestOrders(self.kite, self.leverage, self.order_pct, EXCHANGE)
            db_path = STRATEGY_DB_PATH + LIVE.lower() + "/"

            # opening_time = get_previous_trading_day()
            opening_time = self.opening_time
        elif self.mode == LIVE:
            orders = Orders(self.kite, self.leverage, self.order_pct, EXCHANGE)
            db_path = STRATEGY_DB_PATH + LIVE.lower() + "/"
            opening_time = datetime.datetime.now()
        else:
            raise ValueError("Unknown mode {}".format(self.mode))

        if name == SUPER_TREND_STRATEGY_7_3:
            return SuperTrendStrategyFactory(self.kite, self.mode,
                                             instruments_helper=self.instruments_helper,
                                             db_path=db_path,
                                             orders=self.orders,
                                             opening_time=opening_time).get_strategies(name)
        elif name == PARABOLIC_SAR:
            return ParabolicSARStrategyFactory(self.kite, self.mode,
                                               instruments_helper=self.instruments_helper,
                                               db_path=db_path,
                                               orders=self.orders,
                                               candle_interval=3,
                                               opening_time=opening_time).get_strategies(name)

        elif name == PARABOLIC_SAR_MTF:
            return ParabolicSARMTFStrategyFactory(self.kite, self.mode,
                                                  instruments_helper=self.instruments_helper,
                                                  db_path=db_path,
                                                  orders=self.orders,
                                                  candle_interval_lt=1,
                                                  candle_interval_ht=5,
                                                  opening_time=opening_time).get_strategies(name)

        elif name == ADAPTIVE_SAR_STRATEGY:
            return AdaptiveSARStrategyFactory(self.kite, self.mode,
                                              instruments_helper=self.instruments_helper,
                                              db_path=db_path,
                                              orders=self.orders,
                                              opening_time=opening_time).get_strategies(name)

        elif name == ADX_STRATEGY:
            return ADXStrategyFactory(self.kite, self.mode,
                                      instruments_helper=self.instruments_helper,
                                      db_path=db_path,
                                      orders=self.orders,
                                      opening_time=opening_time).get_strategies(name)

        elif name == SPM_STRATEGY:
            return StructuralPivotMethodStrategyFactory(self.kite, self.mode,
                                                        instruments_helper=self.instruments_helper,
                                                        db_path=db_path,
                                                        orders=self.orders,
                                                        candle_interval=5,
                                                        opening_time=opening_time).get_strategies(name)
