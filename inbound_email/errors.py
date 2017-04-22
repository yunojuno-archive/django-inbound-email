
class RequestParseError(Exception):
    """Error raised when the inbound request could not be parsed."""
    pass


class AttachmentTooLargeError(Exception):
    """Error raised when an attachment is too large."""

    def __init__(self, email, filename, size):
        super(AttachmentTooLargeError, self)
        self.email = email
        self.filename = filename
        self.size = size


class AuthenticationError(Exception):
    """Error raised when the request is not authenticated."""
    pass
