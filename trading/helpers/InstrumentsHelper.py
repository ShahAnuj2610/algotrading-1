import pandas as pd


class InstrumentsHelper:
    def __init__(self, kite, exchange):
        self.kite = kite
        self.exchange = exchange
        self.instruments_df = pd.DataFrame(self.kite.instruments(self.exchange))
        self.instruments_df =\
            self.instruments_df[((self.instruments_df.instrument_type == "EQ") & (self.instruments_df.exchange == exchange))]

        self.symbols_to_instruments = {}
        self.instruments_to_symbols = {}
        for index, row in self.instruments_df.iterrows():
            self.symbols_to_instruments[row['tradingsymbol']] = row['instrument_token']
            self.instruments_to_symbols[row['instrument_token']] = row['tradingsymbol']

    def get_instrument_token_from_symbol(self, symbol):
        # This could be because the sample set might contain a stock that is not listed in the exchange
        # the program assumes
        # For now we focus only on one exchange
        # TODO: Make this code exchange agnostic
        if symbol in self.symbols_to_instruments:
            return self.symbols_to_instruments[symbol]
        else:
            return None

    def get_symbol_from_instrument_token(self, token):
        # This could be because the sample set might contain a stock that is not listed in the exchange
        # the program assumes
        # For now we focus only on one exchange
        # TODO: Make this code exchange agnostic
        if token in self.instruments_to_symbols:
            return self.instruments_to_symbols[token]
        else:
            return None

    def get_instrument_tokens(self, symbols):
        tokens = []

        for s in symbols:
            tokens.append(self.get_instrument_token_from_symbol(s))

        return tokens
