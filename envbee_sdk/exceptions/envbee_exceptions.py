class RequestTimeoutError(Exception):
    def __init__(self, message="Request timed out"):
        self.message = message
        super().__init__(self.message)


class RequestError(Exception):
    def __init__(self, status_code, message="Request error"):
        self.status_code = status_code
        self.message = f"{message}. Status code: {status_code}"
        super().__init__(self.message)
