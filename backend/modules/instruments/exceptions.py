class FetchInstrumentInfoException(Exception):
    def __init__(self, reason: str):
        """
        Initializes the exception with a specific reason for the failure to fetch instrument information.
        
        Args:
            reason: Description of why fetching instrument information failed.
        """
        super().__init__(f"Could not fetch instrument info, reason: {reason}")
        self.reason = reason
