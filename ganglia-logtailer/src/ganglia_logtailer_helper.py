#!/usr/bin/python
"""class for ganglia metric objects to be passed around"""

class GangliaMetricObject(object):
    def __init__(self, name, value, units='', type='float', tmax=60):
        self.name = name
        self.value = value
        self.units = units
        self.type = type
        self.tmax = tmax

class LogtailerParsingException(Exception):
    """Raise this exception if the parse_line function wants to
        throw a 'recoverable' exception - i.e. you want parsing
        to continue but want to skip this line and log a failure."""
    pass

class LogtailerStateException(Exception):
    """Raise this exception if the get_state function has failed.  Metrics from
       this run will not be submitted (since the function did not properly
       return), but reset_state() should have been called so that the metrics
       are valid next time."""
    pass

class LockingError(Exception):
    """ Exception raised for errors creating or destroying lockfiles. """

    def __init__(self, message):
        self.message = message


