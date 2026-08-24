

class PasswordError(Exception):

    def __init__(self, message : str):
        self.message = message
        super().__init__(message)


class LoginError(Exception):

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)