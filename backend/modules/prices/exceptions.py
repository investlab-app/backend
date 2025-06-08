class FetchPriceException(Exception):
    def __init__(self, reason: str):
        """
        Initializes the FetchPriceException with a specific reason for the failure.
        
        Args:
            reason: The explanation for why fetching price data failed.
        """
        super().__init__(f"Could not fetch price data, reason: {reason}")
        self.reason = reason


class InvalidTimeIntervalException(Exception):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason
