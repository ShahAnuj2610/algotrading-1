import logging

from sqlalchemy import create_engine

from trading.constants import SCREENER_DB_PATH
from trading.screener.PreviousDayMaxMover import PreviousDayMaxMover


class ScreenerMain:
    def __init__(self):
        logging.basicConfig(format='%(asctime)s :: %(levelname)s :: %(message)s', level=logging.INFO)

    def screen(self):
        screeners = []
        engine = create_engine(f"sqlite:///"+SCREENER_DB_PATH)

        # Add all your screeners here
        screeners.append(PreviousDayMaxMover(50))

        # Run the screeners
        for screener in screeners:
            df = screener.screen()
            df.to_sql(screener.__class__.__name__, engine, if_exists='replace')

        engine.dispose()
