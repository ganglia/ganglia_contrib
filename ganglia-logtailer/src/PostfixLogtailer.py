###
###  This plugin for logtailer will crunch postfix logs and produce the
###  following metrics:
###    * number of connections per second
###    * number of messages deliveerd per second
###    * number of bounces per second
###

import time
import threading
import re

# local dependencies
from ganglia_logtailer_helper import GangliaMetricObject
from ganglia_logtailer_helper import LogtailerParsingException, LogtailerStateException

class PostfixLogtailer(object):
    # only used in daemon mode
    period = 30.0
    def __init__(self):
        '''This function should initialize any data structures or variables
        needed for the internal state of the line parser.'''
        self.reset_state()
        self.lock = threading.RLock()
        # this is what will match the postfix lines
        # postfix example log format string:
        # connections:
        # Sep 12 13:50:21 host postfix/smtpd[13334]: connect from unknown[1.2.3.4]
        # deliveries:
        # Sep 12 13:39:11 host postfix/local[11393]: E412470C2B8: to=<foo@host>, orig_to=<foo@bar.com>, relay=local, delay=5, delays=1.9/0/0/3.2, dsn=2.0.0, status=sent (delivered to command: /usr/local/bin/procmail)
        # bounces:
        # Sep 12 11:58:52 host postfix/local[18444]: 8D3C671C324: to=<invalid@host>, orig_to=<invalid@bar.com>, relay=local, delay=0.43, delays=0.41/0/0/0.02, dsn=5.1.1, status=bounced (unknown user: "invalid")
        self.reg_connections = re.compile('^.*postfix/smtpd.*connect from unknown.*$')
        self.reg_deliveries = re.compile('^.*postfix/local.* status=sent .*$')
        self.reg_bounces = re.compile('^.*postfix/local.* status=bounced .*$')

        # assume we're in daemon mode unless set_check_duration gets called
        self.dur_override = False


    # example function for parse line
    # takes one argument (text) line to be parsed
    # returns nothing
    def parse_line(self, line):
        '''This function should digest the contents of one line at a time,
        updating the internal state variables.'''
        self.lock.acquire()
        try:
            regMatch = self.reg_connections.match(line)
            if regMatch:
                self.num_connections+=1
            regMatch = self.reg_deliveries.match(line)
            if regMatch:
                self.num_deliveries+=1
            regMatch = self.reg_bounces.match(line)
            if regMatch:
                self.num_bounces+=1
            
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
        myret = dict( num_conns = self.num_connections,
                    num_deliv = self.num_deliveries,
                    num_bounc = self.num_bounces
                    )
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
        self.num_connections = 0
        self.num_deliveries = 0
        self.num_bounces = 0
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

        # crunch data to how you want to report it
        connections_per_second = mydata['num_conns'] / check_time
        deliveries_per_second = mydata['num_deliv'] / check_time
        bounces_per_second = mydata['num_bounc'] / check_time

        # package up the data you want to submit
        cps_metric = GangliaMetricObject('postfix_connections', connections_per_second, units='cps')
        dps_metric = GangliaMetricObject('postfix_deliveries', deliveries_per_second, units='dps')
        bps_metric = GangliaMetricObject('postfix_bounces', bounces_per_second, units='bps')

        # return a list of metric objects
        return [ cps_metric, dps_metric, bps_metric, ]



