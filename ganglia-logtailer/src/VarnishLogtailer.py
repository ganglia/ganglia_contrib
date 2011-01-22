# -*- coding: utf-8 -*-
###
###  This plugin for logtailer will crunch Varnish logs and produce these metrics:
###    * hits per second
###    * GETs per second
###    * number of HTTP 200, 300, 400, and 500 responses per second
###
###  Author: Vladimir Vuksan
###  This script is derivative off Linden Labs' ApacheLogTailer script
###
###  Note that this plugin depends on a Varnish NCSA log format, documented in
###  I am producing the Varnish log by running following command as a daemon
###  /usr/bin/varnishncsa -a -w /var/log/varnish/varnishncsa.log -D -P /var/run/varnishncsa.pid
###
###  To crunch the logs I run following command out of the cron
###
###  /opt/logtailer/ganglia-logtailer --classname VarnishLogtailer --log_file /var/log/varnish/varnishncsa.log --mode cron
##   __init__.

import time
import threading
import re

# local dependencies
from ganglia_logtailer_helper import GangliaMetricObject
from ganglia_logtailer_helper import LogtailerParsingException, LogtailerStateException

class VarnishLogtailer(object):
    # only used in daemon mode
    period = 30
    def __init__(self):
        '''This function should initialize any data structures or variables
        needed for the internal state of the line parser.'''
        self.reset_state()
        self.lock = threading.RLock()
        # this is what will match the apache lines
        # match keys: remote_ip, http_user, http_user2, date, conn_status, init_retcode, final_retcode, size,
        #               req_time, cookie, referrer, request, user_agent, pid
        self.reg = re.compile('^(?P<remote_ip>[^ ]+) (?P<http_user>[^ ]+) (?P<http_user2>[^ ]+) (?P<req_date>[^ ]+) (?P<timezone>[^ ]+) "(?P<request>[^ ]+) (?P<url>[^ ]+) (?P<http_protocol>[^ ]+) (?P<init_retcode>[^ ]+)')
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
        two_per_second = mydata['num_two'] / check_time
        three_per_second = mydata['num_three'] / check_time
        four_per_second = mydata['num_four'] / check_time
        five_per_second = mydata['num_five'] / check_time

        # package up the data you want to submit
        hps_metric = GangliaMetricObject('varnish_hits', hits_per_second, units='hps')
        gps_metric = GangliaMetricObject('varnish_gets', gets_per_second, units='hps')
        twops_metric = GangliaMetricObject('varnish_200', two_per_second, units='hps')
        threeps_metric = GangliaMetricObject('varnish_300', three_per_second, units='hps')
        fourps_metric = GangliaMetricObject('varnish_400', four_per_second, units='hps')
        fiveps_metric = GangliaMetricObject('varnish_500', five_per_second, units='hps')

        # return a list of metric objects
        return [ hps_metric, gps_metric, twops_metric, threeps_metric, fourps_metric, fiveps_metric, ]
