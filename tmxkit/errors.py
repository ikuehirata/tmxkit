"""tmxkit.errors

Module that defines common exceptions used across tmxkit.

Main exceptions:
- ``TmxkitError`` — base exception for tmxkit
- ``TmxParseError`` — raised when parsing TMX/TU fails
- ``InvalidTUError`` — raised when a <tu> structure is different from expected
- ``StreamError`` — raised for errors during TU stream processing
"""


class TmxkitError(Exception):
    """
    Base exception for the tmxkit package.

    Callers may catch this exception to handle all errors originating from
    tmxkit in a uniform way.
    """

    pass


class TmxParseError(TmxkitError):
    """Raised when parsing of TMX or TU fails."""

    pass


class InvalidTUError(TmxkitError):
    """Raised when a <tu> structure does not match expected format."""

    pass


class StreamError(TmxkitError):
    """Raised for errors occurring during TU stream processing."""

    pass
