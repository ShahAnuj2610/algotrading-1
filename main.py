import logging

from trading.ScreenerMain import screen
from trading.TradeMain import trade
from trading.helpers.AccessTokenHelper import AccessTokenHelper
from trading.zerodha.auth.Authorizer import Authorizer


def authorize():
    authorizer = Authorizer(AccessTokenHelper())
    _kite = authorizer.get_authorized_kite_object()
    logging.info("Authorized with kite connect successfully")
    return _kite


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s :: %(levelname)s :: %(message)s', level=logging.INFO)

    kite = authorize()
    # screen(kite)
    trade(kite)

