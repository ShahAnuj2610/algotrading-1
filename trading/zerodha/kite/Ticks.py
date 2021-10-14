from trading.helpers.TicksDB import TicksDB


class Ticks:
    def __init__(self, symbols, instruments_helper):
        self.tokens = instruments_helper.get_instrument_tokens(symbols)
        self.instruments_helper = instruments_helper

    def on_ticks(self, ws, ticks):
        ticks_db = TicksDB(self.instruments_helper)
        ticks_db.insert_ticks(ticks)
        ticks_db.close()

    def on_connect(self, ws, response):
        ws.subscribe(self.tokens)
