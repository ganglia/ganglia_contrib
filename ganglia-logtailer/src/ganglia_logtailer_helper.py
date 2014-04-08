#!/usr/bin/python
"""class for ganglia metric objects to be passed around"""
import re

class GangliaMetricObject(object):
    def __init__(self, name, value, units='', type='float', tmax=60, dmax=0):
        self.name = name
        self.value = value
        self.units = units
        self.type = type
        self.tmax = tmax
        self.dmax = dmax
    def set_value(self, value):
        self.value = value
    def dump_dict(self):
        """serialize this object to a dictionary"""
        return self.__dict__
    def set_from_dict(self, hashed_object):
        """recreate object from dict"""
        self.name = hashed_object["name"]
        self.value = hashed_object["value"]
        self.units = hashed_object["units"]
        self.type = hashed_object["type"]
        self.tmax = hashed_object["tmax"]
        self.dmax = hashed_object["dmax"]
    def sanitize_metric_name(self):
        """sanitize metric names by translating all non alphanumerics to underscore"""
        self.name = re.sub("[^A-Za-z0-9._-]", "_", self.name)
    def __eq__(self, other):
        """A ganglia metric object is equivalent if the name is the same."""
        return self.name == other.name

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

class SavedMetricsException(Exception):
    """Raise this exception if there's a problem recovering the saved metric
        list from the statedir. This will always happen on the first run, and
        should be ignored. On subsequent runs, it probably means a config
        problem where the statedir can't be written or something."""
    pass

class LockingError(Exception):
    """ Exception raised for errors creating or destroying lockfiles. """

    def __init__(self, message):
        self.message = message


