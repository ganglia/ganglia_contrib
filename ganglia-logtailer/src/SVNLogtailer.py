# -*- coding: utf-8 -*-
###
###  This plugin for logtailer will crunch apache logs for SVN and produce these metrics:
###    * hits per second
###    * GET, PROPPATCH, PROPFINDs etc. per second
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

class SVNLogtailer(object):
    # only used in daemon mode
    period = 30
    def __init__(self):
        '''This function should initialize any data structures or variables
        needed for the internal state of the line parser.'''
        self.reset_state()
        self.lock = threading.RLock()
        # this is what will match the apache lines
        # apache log format string:
	# %{X-Forwarded-For}i %l %{%Y-%m-%d-%H:%M:%S}t \"%r\" %>s %B \"%{Referer}i\" \"%{User-Agent}i\" %D
        self.reg = re.compile('(?P<remote_ip>[^ ]+) (?P<user>[^ ]+) (?P<user2>[^ ]+) \[(?P<date>[^\]]+)\] "(?P<request>[^ ]+) (?P<url>[^ ]+) (?P<http_protocol>[^ ]+)" (?P<init_retcode>[^ ]+) (?P<size>[^ ]+)')

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
                elif( 'POST' in linebits['request'] ):
                    self.num_posts+=1
                elif( 'PROPFIND' in linebits['request'] ):
                    self.num_propfind+=1
                elif( 'OPTIONS' in linebits['request'] ):
                    self.num_options+=1
                elif( 'PUT' in linebits['request'] ):
                    self.num_put+=1
                elif( 'REPORT' in linebits['request'] ):
                    self.num_report+=1
                elif( 'DELETE' in linebits['request'] ):
                    self.num_delete+=1
                elif( 'PROPPATCH' in linebits['request'] ):
                    self.num_proppatch+=1
                elif( 'CHECKOUT' in linebits['request'] ):
                    self.num_checkout+=1
                elif( 'MERGE' in linebits['request'] ):
                    self.num_merge+=1
                elif( 'MKACTIVITY' in linebits['request'] ):
                    self.num_mkactivity+=1
                elif( 'COPY' in linebits['request'] ):
                    self.num_copy+=1
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
		    num_posts=self.num_posts,
		    num_propfind=self.num_propfind,
		    num_options=self.num_options,
		    num_put=self.num_put,
		    num_report=self.num_report,
		    num_delete=self.num_delete,
		    num_proppatch=self.num_proppatch,
		    num_checkout=self.num_checkout,
		    num_merge=self.num_merge,
		    num_mkactivity=self.num_mkactivity,
		    num_copy=self.num_copy,
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
        self.num_posts = 0
        self.num_propfind = 0
        self.num_options = 0
        self.num_put = 0
        self.num_report = 0
        self.num_delete = 0
        self.num_proppatch = 0
        self.num_checkout = 0
        self.num_merge = 0
        self.num_mkactivity = 0
        self.num_copy = 0
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
        hits_gets_ps = mydata['num_gets'] / check_time 
        hits_posts_ps = mydata['num_posts'] / check_time 
        hits_propfind_ps = mydata['num_propfind'] / check_time 
        hits_options_ps = mydata['num_options'] / check_time 
        hits_put_ps = mydata['num_put'] / check_time 
        hits_report_ps = mydata['num_report'] / check_time 
        hits_delete_ps = mydata['num_delete'] / check_time 
        hits_proppatch_ps = mydata['num_proppatch'] / check_time 
        hits_checkout_ps = mydata['num_checkout'] / check_time 
        hits_merge_ps = mydata['num_merge'] / check_time 
        hits_mkactivity_ps = mydata['num_mkactivity'] / check_time 
        hits_copy_ps = mydata['num_copy'] / check_time 
        
        # 
        two_per_second = mydata['num_two'] / check_time
        three_per_second = mydata['num_three'] / check_time 
        four_per_second = mydata['num_four'] / check_time
        five_per_second = mydata['num_five'] / check_time

        # package up the data you want to submit
        hps_metric = GangliaMetricObject('svn_total', hits_per_second, units='hps')
        gets_metric = GangliaMetricObject('svn_gets', hits_gets_ps, units='hps')
        posts_metric = GangliaMetricObject('svn_posts', hits_posts_ps, units='hps')
        propfind_metric = GangliaMetricObject('svn_propfind', hits_propfind_ps, units='hps')
        options_metric = GangliaMetricObject('svn_options', hits_options_ps, units='hps')
        put_metric = GangliaMetricObject('svn_put', hits_put_ps, units='hps')
        report_metric = GangliaMetricObject('svn_report', hits_report_ps, units='hps')
        delete_metric = GangliaMetricObject('svn_delete', hits_delete_ps, units='hps')
        proppatch_metric = GangliaMetricObject('svn_proppatch', hits_proppatch_ps, units='hps')
        checkout_metric = GangliaMetricObject('svn_checkout', hits_checkout_ps, units='hps')
        merge_metric = GangliaMetricObject('svn_merge', hits_merge_ps, units='hps')
        mkactivity_metric = GangliaMetricObject('svn_mkactivity', hits_mkactivity_ps, units='hps')
        copy_metric = GangliaMetricObject('svn_copy', hits_copy_ps, units='hps')
        
        twops_metric = GangliaMetricObject('svn_200', two_per_second, units='hps')
        threeps_metric = GangliaMetricObject('svn_300', three_per_second, units='hps')
        fourps_metric = GangliaMetricObject('svn_400', four_per_second, units='hps')
        fiveps_metric = GangliaMetricObject('svn_500', five_per_second, units='hps')

        # return a list of metric objects
        return [ hps_metric, gets_metric, posts_metric, propfind_metric, options_metric, put_metric, report_metric, delete_metric, proppatch_metric, checkout_metric, merge_metric, mkactivity_metric, copy_metric, twops_metric, threeps_metric, fourps_metric, fiveps_metric, ]



