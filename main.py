import logging

from trading.BackTestMain import back_test
from trading.ScreenerMain import screen
from trading.SetupMain import set_up
from trading.TradeMain import trade
from trading.constants import EXCHANGE
from trading.helpers.AccessTokenHelper import AccessTokenHelper
from trading.helpers.InstrumentsHelper import InstrumentsHelper
from trading.zerodha.auth.Authorizer import Authorizer


def authorize():
    authorizer = Authorizer(AccessTokenHelper())
    _kite = authorizer.get_authorized_kite_object()
    logging.info("Authorized with kite connect successfully")
    return _kite


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s :: %(levelname)s :: %(message)s', level=logging.INFO)

    kite = authorize()
    instruments_helper = InstrumentsHelper(kite, EXCHANGE)

    back_test(kite, instruments_helper)

    # screen(kite)
    # set_up(kite, instruments_helper)
    # trade(kite)

