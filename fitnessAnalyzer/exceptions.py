class InvalidIdentifierError(ValueError):
    "Raised when an identifier has an invalid format"

    def __init__(self, field, message):
        super().__init__(message)
        self.field = field

class InvalidRecordError(ValueError):
    "Raised when a CSV record cant be accepted"

    def __init__(self, field, message):
        super().__init__(message)
        self.field = field