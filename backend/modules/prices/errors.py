class FetchPriceException(Exception):
    def __init__(self, reason: str):
        super().__init__(f"Could not fetch data from yfinance, reason: {reason}")
        self.reason = reason


class InvalidTimeIntervalException(Exception):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


class IllegalDateOrderException(Exception):
    def __init__(self):
        super().__init__(f"End date cannot preceed start date")
