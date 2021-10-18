from sqlalchemy import create_engine

from trading.constants import SCREENER_DB_PATH, SCREEN
from trading.screener.PreviousDayMaxMover import PreviousDayMaxMover


def screen(kite):
    screeners = []
    engine = create_engine(f"sqlite:///"+SCREENER_DB_PATH)

    # Add all your screeners here
    screeners.append(PreviousDayMaxMover(50, kite))

    # Run the screeners
    for screener in screeners:
        df = screener.screen()
        df.to_sql(screener.__class__.__name__, engine, if_exists='replace')

    engine.dispose()
