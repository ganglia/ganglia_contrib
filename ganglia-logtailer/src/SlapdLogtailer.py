###
###   a 'metric object' is an instance of GangliaMetricObject
###       { 'name' => 'name-of-metric',
###         'value' => numerical-or-string-value,
###         'type' => 'int32',    <--- see gmetric man page for valid types
###         'units' => 'qps',     <--- label on the graph
###         }
###   This object should appear remarkably similar to the required arguments to gmetric.
###
###
###   The logtailer class must define
###     a class variable 'period'
###     an instance method set_check_duration that sets the time since last invocation (used in cron mode)
###     an instance method get_state() that returns a list of metric objects
###     an instance method parse_line(line) that takes one line of the log file and does whatever internal accounting is necessary to record its metrics
###   The logtailer class must be thread safe - a separate thread will be calling get_state() and parse_line(line)
###   parse_line(line) may raise a LogtailerParsingException to log an error and discard the current line but keep going.  Any other exception will kill the process.
###

import time
import threading
import re

# local dependencies
from ganglia_logtailer_helper import GangliaMetricObject
from ganglia_logtailer_helper import LogtailerParsingException, LogtailerStateException

class SlapdLogtailer(object):
    # period must be defined and indicates how often the gmetric thread should call get_state() (in seconds) (in daemon mode only)
    # note that if period is shorter than it takes to run get_state() (if there's lots of complex calculation), the calling thread will automatically double period.
    # period ought to be >=5.  It should probably be >=60 (to avoid excessive load).  120 to 300 is a good range (2-5 minutes).  Take into account the need for time resolution, as well as the number of hosts reporting (6000 hosts * 15s == lots of data).
    period = 300
    def __init__(self):
        '''This function should initialize any data structures or variables
        needed for the internal state of the line parser.'''
        self.reset_state()
        self.lock = threading.RLock()
        # Oct 27 13:34:30 ldap0.lindenlab.com slapd[16533]: conn=0 fd=18 ACCEPT from IP=216.82.33.42:60976 (IP=0.0.0.0:636)
        self.reg = re.compile('^.*lindenlab.com slapd\[\d+\]: .*(?P<query_status>ACCEPT from IP)')
        self.dur_override = False
        
    # example function for parse line
    # takes one argument (text) line to be parsed
    # returns nothing
    def parse_line(self, line):
        '''This function should digest the contents of one line at a time,
        updating the internal state variables.'''
        self.lock.acquire()
        try:
            regMatch = self.reg.match(line)
            #print regMatch
            if regMatch:
                linebits = regMatch.groupdict()
                if( 'ACCEPT from IP' in linebits['query_status'] ):
                    self.num_slapdquery += 1
            else:
                pass
        except Exception, e:
            self.lock.release()
            raise LogtailerParsingException, "regmatch or contents failed with %s" % e
        self.lock.release()

    # example function for deep copy
    # takes no arguments
    # returns one object
    def deep_copy(self):
        '''This function should return a copy of the data structure used to
        maintain state.  This copy should different from the object that is
        currently being modified so that the other thread can deal with it
        without fear of it changing out from under it.  The format of this
        object is internal to the plugin.'''
        myret = dict(num_slapdquery = self.num_slapdquery)
        return myret
    # example function for reset_state
    # takes no arguments
    # returns nothing
    def reset_state(self):
        '''This function resets the internal data structure to 0 (saving
        whatever state it needs).  This function should be called
        immediately after deep copy with a lock in place so the internal
        data structures can't be modified in between the two calls.  If the
        time between calls to get_state is necessary to calculate metrics,
        reset_state should store now() each time it's called, and get_state
        will use the time since that now() to do its calculations'''
        self.num_slapdquery = 0
        self.last_reset_time = time.time()
    # example for keeping track of runtimes
    # takes no arguments
    # returns float number of seconds for this run
    def set_check_duration(self, dur):
        '''This function only used if logtailer is in cron mode.  If it is
        invoked, get_check_duration should use this value instead of calculating
        it.'''
        self.duration = dur
        self.dur_override = True
    def get_check_duration(self):
        '''This function should return the time since the last check.  If called
        from cron mode, this must be set using set_check_duration().  If in
        daemon mode, it should be calculated internally.'''
        if( self.dur_override ):
            duration = self.duration
        else:
            cur_time = time.time()
            duration = cur_time - self.last_reset_time
            # the duration should be within 10% of period
            acceptable_duration_min = self.period - (self.period / 10.0)
            acceptable_duration_max = self.period + (self.period / 10.0)
            if (duration < acceptable_duration_min or duration > acceptable_duration_max):
                raise LogtailerStateException, "time calculation problem - duration (%s) > 10%% away from period (%s)" % (duration, self.period)
        return duration
    # example function for get_state
    # takes no arguments
    # returns a dictionary of (metric => metric_object) pairs
    def get_state(self):
        '''This function should acquire a lock, call deep copy, get the
        current time if necessary, call reset_state, then do its
        calculations.  It should return a list of metric objects.'''
        # get the data to work with
        self.lock.acquire()
        try:
            mydata = self.deep_copy()
            check_time = self.get_check_duration()
            self.reset_state()
            self.lock.release()
        except LogtailerStateException, e:
            # if something went wrong with deep_copy or the duration, reset and continue
            self.reset_state()
            self.lock.release()
            raise e

        # normalize to queries per second
        slapdquery = mydata['num_slapdquery'] / check_time
        #print slapdquery

        # package up the data you want to submit
        slapdquery_metric = GangliaMetricObject('slapd_queries', slapdquery, units='qps')
        # return a list of metric objects
        return [ slapdquery_metric, ]



