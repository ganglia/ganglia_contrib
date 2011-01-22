# -*- coding: utf-8 -*-
###
###  Author: Vladimir Vuksan
###  This plugin for logtailer will crunch Java GC logs (modified from PostfixLogtailer)
###    * number of minor GC events
###    * number of full GC events
###    * number of broken GC events
###    * GC time in seconds
###    * Number of garbage bytes collected

import time
import threading
import re

# local dependencies
from ganglia_logtailer_helper import GangliaMetricObject
from ganglia_logtailer_helper import LogtailerParsingException, LogtailerStateException

class JavaGCLogtailer(object):
    # only used in daemon mode
    period = 30.0
    def __init__(self):
        '''This function should initialize any data structures or variables
        needed for the internal state of the line parser.'''
        self.reset_state()
        self.lock = threading.RLock()
        # this is what will match the Java GC lines
        # Minor GC event 
        # 1097.790: [GC 274858K->16714K(508288K), 0.0146880 secs]
	# Broken GC even
	# 4.762: [GC 98158K(5240768K), 0.0152010 secs]
	# Full GC
	# 3605.198: [Full GC 16722K->16645K(462400K), 0.1874650 secs]
        self.reg_minor_gc = re.compile('^.*: \[GC (?P<start_size>[^ ]+)K->(?P<end_size>[^ ]+)K\((?P<heap_size>[^ ]+)\), (?P<gc_time>[^ ]+) secs\]$')
        self.reg_broken_gc = re.compile('^.*: \[GC (?P<start_size>[0-9]+)K\((?P<heap_size>[^ ]+)\), (?P<gc_time>[^ ]+) secs\]$')
        self.reg_full_gc = re.compile('^.*: \[Full GC (?P<start_size>[^ ]+)K->(?P<end_size>[^ ]+)K\((?P<heap_size>[^ ]+)\), (?P<gc_time>[^ ]+) secs\]$')

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
            regMatch = self.reg_minor_gc.match(line)
            if regMatch:
                linebits = regMatch.groupdict()
                self.minor_gc+=1
                self.gc_time+= float(linebits['gc_time'])
                self.garbage+= int(linebits['start_size']) - int(linebits['end_size'])
            regMatch = self.reg_broken_gc.match(line)
            if regMatch:
                linebits = regMatch.groupdict()
                self.broken_gc+=1
                self.gc_time+= float(linebits['gc_time'])
            regMatch = self.reg_full_gc.match(line)
            if regMatch:
                linebits = regMatch.groupdict()
                self.full_gc+=1
                self.gc_time+= float(linebits['gc_time'])
                self.garbage+= int(linebits['start_size']) - int(linebits['end_size'])
            
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
        myret = dict( gc_time = self.gc_time,
                    minor_gc = self.minor_gc,
                    full_gc = self.full_gc,
                    broken_gc = self.broken_gc,
                    garbage = self.garbage
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
        self.minor_gc = 0
        self.broken_gc = 0
        self.full_gc = 0
        self.gc_time = 0
        self.garbage = 0
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
        garbage = float(mydata['garbage']) * 1000

        # package up the data you want to submit
        full_gc_metric = GangliaMetricObject('gc_full', mydata['full_gc'] , units='events')
        minor_gc_metric = GangliaMetricObject('gc_minor', mydata['minor_gc'] , units='events')
        broken_gc_metric = GangliaMetricObject('gc_broken', mydata['broken_gc'] , units='events')
        gc_time_metric = GangliaMetricObject('gc_time', mydata['gc_time'] , units='seconds')
        garbage_metric = GangliaMetricObject('gc_garbage', garbage , units='bytes')

        # return a list of metric objects
        return [ full_gc_metric, minor_gc_metric, broken_gc_metric, gc_time_metric, garbage_metric ]



