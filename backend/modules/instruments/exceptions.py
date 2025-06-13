class FetchInstrumentInfoException(Exception):
    def __init__(self, reason: str):
        super().__init__(f"Could not fetch instrument info, reason: {reason}")
        self.reason = reason


class FetchInstrumentNewsException(Exception):
    def __init__(self, reason: str):
        super().__init__(f"Could not fetch instrument news, reason: {reason}")
        self.reason = reason
