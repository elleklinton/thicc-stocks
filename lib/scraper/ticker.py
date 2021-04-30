class Ticker:
    def __init__(self, ticker, name):
        self.ticker = ticker
        self.name = name


class CommonTickers:
    APPLE = Ticker('AAPL', "Apple")
    GM = Ticker('GM', "General-Motors")
    ATT = Ticker('T', "ATT")
    SPY = Ticker('SPY', "SP500")
    MICROSOFT = Ticker('MSFT', "Microsoft")
    DISNEY = Ticker('DIS', 'Disney')
    PROCTOR_AND_GAMBLE = Ticker('PG', 'Proctor-And-Gamble')
