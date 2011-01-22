# -*- coding: utf-8 -*-
###
###  This plugin for logtailer will crunch apache logs and produce these metrics:
###    * hits per second
###    * GETs per second
###    * average query processing time
###    * ninetieth percentile query processing time
###    * number of HTTP 200, 300, 400, and 500 responses per second
###
###  Note that this plugin depends on a certain apache log format, documented in
##   __init__.

import time
import threading
import re

# local dependencies
from ganglia_logtailer_helper import GangliaMetricObject
from ganglia_logtailer_helper import LogtailerParsingException, LogtailerStateException

class ApacheLogtailer(object):
    # only used in daemon mode
    period = 30
    def __init__(self):
        '''This function should initialize any data structures or variables
        needed for the internal state of the line parser.'''
        self.reset_state()
        self.lock = threading.RLock()
        # this is what will match the apache lines
        # apache log format string:
        # %v %A %a %u %{%Y-%m-%dT%H:%M:%S}t %c %s %>s %B %D %{cookie}n \"%{Referer}i\" \"%r\" \"%{User-Agent}i\" %P
        # host.com 127.0.0.1 127.0.0.1 - 2008-05-08T07:34:44 - 200 200 371 103918 - "-" "GET /path HTTP/1.0" "-" 23794
        # match keys: server_name, local_ip, remote_ip, date, conn_status, init_retcode, final_retcode, size,
        #               req_time, cookie, referrer, request, user_agent, pid
        self.reg = re.compile('^(?P<server_name>[^ ]+) (?P<local_ip>[^ ]+) (?P<remote_ip>[^ ]+) (?P<user>[^ ]+) (?P<date>[^ ]+) (?P<conn_status>[^ ]+) (?P<init_retcode>[^ ]+) (?P<final_retcode>[^ ]+) (?P<size>[^ ]+) (?P<req_time>[^ ]+) (?P<cookie>[^ ]+) "(?P<referrer>[^"]+)" "(?P<request>[^"]+)" "(?P<user_agent>[^"]+)" (?P<pid>[^ ]+)')

        # assume we're in daemon mode unless set_check_duration gets called
        self.dur_override = False


    # example function for parse line
    # takes one argument (text) line to be parsed
    # returns nothing
    def parse_line(self, line):
        '''This function should digest the contents of one line at a time,
        updating the internal state variables.'''
        self.lock.acquire()
        self.num_hits+=1
        try:
            regMatch = self.reg.match(line)
            if regMatch:
                linebits = regMatch.groupdict()
                # capture GETs
                if( 'GET' in linebits['request'] ):
                    self.num_gets+=1
                # capture HTTP response code
                rescode = float(linebits['init_retcode'])
                if( (rescode >= 200) and (rescode < 300) ):
                    self.num_two+=1
                elif( (rescode >= 300) and (rescode < 400) ):
                    self.num_three+=1
                elif( (rescode >= 400) and (rescode < 500) ):
                    self.num_four+=1
                elif( (rescode >= 500) and (rescode < 600) ):
                    self.num_five+=1
                # capture request duration
                dur = float(linebits['req_time'])
                # convert to seconds
                dur = dur / 1000000
                self.req_time += dur
                # store for 90th % calculation
                self.ninetieth.append(dur)
            else:
                raise LogtailerParsingException, "regmatch failed to match"
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
                    num_gets=self.num_gets,
                    req_time=self.req_time,
                    num_two=self.num_two,
                    num_three=self.num_three,
                    num_four=self.num_four,
                    num_five=self.num_five,
                    ninetieth=self.ninetieth
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
        self.num_gets = 0
        self.req_time = 0
        self.num_two = 0
        self.num_three = 0
        self.num_four = 0
        self.num_five = 0
        self.ninetieth = list()
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
        hits_per_second = mydata['num_hits'] / check_time
        gets_per_second = mydata['num_gets'] / check_time
        if (mydata['num_hits'] != 0):
             avg_req_time = mydata['req_time'] / mydata['num_hits']
        else:
             avg_req_time = 0
        two_per_second = mydata['num_two'] / check_time
        three_per_second = mydata['num_three'] / check_time
        four_per_second = mydata['num_four'] / check_time
        five_per_second = mydata['num_five'] / check_time

        # calculate 90th % request time
        ninetieth_list = mydata['ninetieth']
        ninetieth_list.sort()
        num_entries = len(ninetieth_list)
        if (num_entries != 0 ):
             ninetieth_element = ninetieth_list[int(num_entries * 0.9)]
        else:
             ninetieth_element = 0

        # package up the data you want to submit
        hps_metric = GangliaMetricObject('apache_hits', hits_per_second, units='hps')
        gps_metric = GangliaMetricObject('apache_gets', gets_per_second, units='hps')
        avgdur_metric = GangliaMetricObject('apache_avg_dur', avg_req_time, units='sec')
        ninetieth_metric = GangliaMetricObject('apache_90th_dur', ninetieth_element, units='sec')
        twops_metric = GangliaMetricObject('apache_200', two_per_second, units='hps')
        threeps_metric = GangliaMetricObject('apache_300', three_per_second, units='hps')
        fourps_metric = GangliaMetricObject('apache_400', four_per_second, units='hps')
        fiveps_metric = GangliaMetricObject('apache_500', five_per_second, units='hps')

        # return a list of metric objects
        return [ hps_metric, gps_metric, avgdur_metric, ninetieth_metric, twops_metric, threeps_metric, fourps_metric, fiveps_metric, ]



