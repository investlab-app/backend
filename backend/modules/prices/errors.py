class UnknownTickerError(Exception):
    def __init__(self, ticker: str):
        super().__init__(f"Unknown ticker: {ticker}")
        self.ticker = ticker

class IllegalDateOrderException(Exception):
    def __init__(self):
        super().__init__(f"End date cannot preceed start date")