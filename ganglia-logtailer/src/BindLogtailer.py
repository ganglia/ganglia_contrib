###
###  This plugin for logtailer crunches bind's log and produces these metrics:
###    * queries per second
###    * number of unique clients seen in the sampling period, normalized over
###      the sampling time
###    * number of requests by the client that made the most requests
###

import time
import threading
import re

# local dependencies
from ganglia_logtailer_helper import GangliaMetricObject
from ganglia_logtailer_helper import LogtailerParsingException, LogtailerStateException

class BindLogtailer(object):
    # only used in daemon mode
    period = 30.0
    def __init__(self):
        '''This function should initialize any data structures or variables
        needed for the internal state of the line parser.'''
        self.reset_state()
        self.lock = threading.RLock()
        # this is what will match the backbone lines
        # backbone log example:
        # Sep 11 09:03:05 ns0-sfo.lindenlab.com named[577]: client 80.189.94.233#49199: query: secondlife.com IN A
        # match keys: client_ip
        self.reg = re.compile('^.*named.*client (?P<client_ip>[0-9\.]+).*query')

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
            regMatch = self.reg.match(line)
            if regMatch:
                linebits = regMatch.groupdict()
                self.num_hits+=1
                self.client_ip_list.append(linebits['client_ip'])
            else:
                # this occurs for every non-named query line.  Ignore them.
                #raise LogtailerParsingException, "regmatch failed to match line (%s)" % line
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
        myret = dict( num_hits=self.num_hits,
                      client_ip_list=self.client_ip_list,
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
        self.num_hits = 0
        self.last_reset_time = time.time()
        self.client_ip_list = list()
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
        queries_per_second = mydata['num_hits'] / check_time

        # calculate number of querying IPs and maximum number of queries per IP
        clist = mydata['client_ip_list']

        cdict = dict()
        for elem in clist:
            cdict[elem] = cdict.get(elem,0) + 1

        # number of unique clients connecting, normalized to per minute
        num_client_ips = len(cdict) / check_time
        # number of requests issued by the client making the most
        max_client_ip_count = max(cdict.values()) / check_time


        # package up the data you want to submit
        qps_metric = GangliaMetricObject('bind_queries', queries_per_second, units='qps')
        clients_metric = GangliaMetricObject('bind_num_clients', num_client_ips, units='cps')
        max_reqs_metric = GangliaMetricObject('bind_largest_volume_client', max_client_ip_count, units='qps')

        # return a list of metric objects
        return [ qps_metric, clients_metric, max_reqs_metric, ]



