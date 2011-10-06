#!/usr/bin/python


#+++ scriptim exceptions +++

class ScriptimException(Exception):
    """Base class for every scriptim exception."""
    pass

class ReaderAbsentException(ScriptimException):
    """raised when a reader that should be there isn't"""
    pass

class NoMoreFiltersException(ScriptimException):
    """raised by the FilterChain when it is asked to run more filters and there
is no more Filters to execute
"""


