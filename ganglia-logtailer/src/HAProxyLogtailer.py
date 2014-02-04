import time
import threading
import re
import copy

# local dependencies
from ganglia_logtailer_helper import GangliaMetricObject
from ganglia_logtailer_helper import LogtailerParsingException, LogtailerStateException

class HAProxyLogtailer(object):
    # only used in daemon mode
    period = 30
    def __init__(self):
        '''This function should initialize any data structures or variables
        needed for the internal state of the line parser.'''
        self.lock = threading.RLock()

        # example:
        # Jan 24 20:17:25 localhost haproxy[6844]: 127.0.0.1:39747 [24/Jan/2014:20:17:25.210] apps apps/app711 0/0/0/156/156 200 602 - - ---- 169/166/166/0/0 0/0 "POST /1/comm HTTP/1.0"
        # Jan 24 20:17:25 localhost haproxy[6844]: 127.0.0.1:45684 [24/Jan/2014:20:17:25.357] rails rails/rails2 0/0/3/6/10 200 900 - - ---- 168/2/2/0/0 0/0 "GET / HTTP/1.0"
        # things we're looking for:
        # global active connection count (168/169 in these examples) (min/max/avg)
        # global hit count
        # per-listener feconn and beconn (the second and third numbers in the second #/#/#/#/# stanza) (min/max/avg)
        # per-listener hit count
        # per-listener latency metrics - total connection time (Tt) metric (the last number in the first #/#/#/#/# stanza) (min/max/avg/50th/90th)
        # per-listener per-response code hit count (group hundreds, eg 4xx, 3xx)
        logformat = '^(?P<date1>... .. ..:..:..) (?P<hostname>[^ ]*) haproxy\[(?P<pid>\d+)\]: (?P<ipaddr>[0-9.]+):(?P<port>\d+) '
        logformat += '(?P<date2>[^ ]+) (?P<frontend>[^ ]+) (?P<backend>[^ ]+)/(?P<server>[^ ]+) '
        logformat += '(?P<tq>\d+)/(?P<tw>\d+)/(?P<tc>\d+)/(?P<tr>\d+)/(?P<tt>\d+) '
        logformat += '(?P<response_code>\d+) (?P<bytes>\d+) - - ---- '
        logformat += '(?P<actconn>\d+)/(?P<feconn>\d+)/(?P<beconn>\d+)/(?P<srvconn>\d+)/(?P<retries>\d+) (?P<srvqueue>\d+)/(?P<bequeue>\d+) '
        logformat += '(?P<request>.*)$'
        self.reg = re.compile(logformat)

        self.metricshash = {}
        self.global_actconn = [] #this is a list of active connections, from which we calculate min/max/avg at the end
        self.global_hits = 0
        self.listeners = {}
        self.response_codes = ['2xx', '3xx', '4xx', '5xx', 'other']
        # example substructure
        # listeners["parse.com"] = {}
        # # hit count is the length of any of these three arrays; they should all be the same
        # listeners["parse.com"]["latency"] = []
        # listeners["parse.com"]["feconn"] = []
        # listeners["parse.com"]["beconn"] = []
        # listeners["parse.com"]["responses"] = {'2xx':[], '3xx':[], '4xx':[], '5xx':[]}

        #print logformat
        # assume we're in daemon mode unless set_check_duration gets called
        self.dur_override = False
        self.reset_state()

    # example function for parse line
    # takes one argument (text) line to be parsed
    # returns nothing
    def parse_line(self, line):
        '''This function should digest the contents of one line at a time,
        updating the internal state variables.'''
        self.lock.acquire()

        reg = self.reg
        try:
            regMatch = reg.match(line)
        except Exception, e:
            self.lock.release()
            # this happens a lot in this file, just return and go on to the next line.
            return

        if regMatch:
            lineBits = regMatch.groupdict()
            self.global_hits += 1
            self.global_actconn.append(int(lineBits['actconn']))

            if lineBits['response_code'].startswith('2'):
                response_code = "2xx"
            elif lineBits['response_code'].startswith('3'):
                response_code = "3xx"
            elif lineBits['response_code'].startswith('4'):
                response_code = "4xx"
            elif lineBits['response_code'].startswith('5'):
                response_code = "5xx"
            else:
                response_code = "other"

            try:
                self.listeners[lineBits['frontend']]['latency'].append(int(lineBits['tt']))
            except KeyError:
                # first time seeing this listener; create the data structure
                self.listeners[lineBits['frontend']] = {}
                self.listeners[lineBits['frontend']]["name"] = lineBits['frontend']
                self.listeners[lineBits['frontend']]["latency"] = []
                self.listeners[lineBits['frontend']]["feconn"] = []
                self.listeners[lineBits['frontend']]["beconn"] = []
                self.listeners[lineBits['frontend']]["responses"] = {}
                for code in self.response_codes:
                    self.listeners[lineBits['frontend']]["responses"][code] = 0
                # ok, now re-add the entry
                self.listeners[lineBits['frontend']]['latency'].append(int(lineBits['tt']))
            self.listeners[lineBits['frontend']]["feconn"].append(int(lineBits['feconn']))
            self.listeners[lineBits['frontend']]["beconn"].append(int(lineBits['beconn']))
            self.listeners[lineBits['frontend']]["responses"][response_code] += 1

        else:
            self.lock.release()
            return

        self.lock.release()


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

        self.last_reset_time = time.time()
        self.metricshash = {}
        self.global_actconn = []
        self.global_hits = 0
        self.listeners = {}


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
        if (self.dur_override):
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


    def add_metric(self, name, val):
        self.metricshash[name] = val

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
            global_actconn = copy.deepcopy(self.global_actconn)
            global_hits = self.global_hits
            listeners = copy.deepcopy(self.listeners)
            check_time = self.get_check_duration()
            self.reset_state()
            self.lock.release()
        except LogtailerStateException, e:
            # if something went wrong with deep_copy or the duration, reset and continue
            self.reset_state()
            self.lock.release()
            raise e

        results  = []       # A list for all the Ganglia Log objects

        # if check_time is 0, skip this round because if there's no time, there's no stats..
        if check_time == 0:
            print "check_time is zero, which shouldn't happen.  skipping this run."
            return results

        if global_hits == 0:
            # if there are no hits, skip everything else
            self.add_metric('haproxy_total_hits', 0)
        else:
            # calculate min/max/avg for global active connections
            self.add_metric('haproxy_total_hits', float(global_hits) / check_time)
            global_actconn.sort()
            global_actconn_min = global_actconn[0]
            global_actconn_max = global_actconn[-1]
            global_actconn_avg = float(sum(global_actconn)) / global_hits

            self.add_metric('haproxy_active_connections_min', global_actconn_min)
            self.add_metric('haproxy_active_connections_max', global_actconn_max)
            self.add_metric('haproxy_active_connections_avg', global_actconn_avg)

            for name, listener in listeners.iteritems():
                self.add_metric('haproxy_%s_hits' % name, float(len(listener["latency"])) / check_time)
                # percentage of total hits from this listener 
                self.add_metric('haproxy_%s_hits_p' % name, float(len(listener["latency"])) / global_hits * 100)
                latency = listener["latency"]
                latency.sort()
                # latency is recorded in millisec; convert it to seconds
                self.add_metric('haproxy_%s_latency_%s' % (name, 'min'), float(latency[0])/1000)
                self.add_metric('haproxy_%s_latency_%s' % (name, 'max'), float(latency[-1])/1000)
                self.add_metric('haproxy_%s_latency_%s' % (name, 'avg'), float(sum(latency)) / len(latency)/1000)
                self.add_metric('haproxy_%s_latency_%s' % (name, '50th'), float(latency[int(len(latency) * 0.5)])/1000)
                self.add_metric('haproxy_%s_latency_%s' % (name, '90th'), float(latency[int(len(latency) * 0.9)])/1000)
                feconn = listener["feconn"]
                feconn.sort()
                self.add_metric('haproxy_%s_feconn_%s' % (name, 'min'), feconn[0])
                self.add_metric('haproxy_%s_feconn_%s' % (name, 'max'), feconn[-1])
                self.add_metric('haproxy_%s_feconn_%s' % (name, 'avg'), float(sum(feconn)) / len(feconn))
                beconn = listener["beconn"]
                beconn.sort()
                self.add_metric('haproxy_%s_beconn_%s' % (name, 'min'), beconn[0])
                self.add_metric('haproxy_%s_beconn_%s' % (name, 'max'), beconn[-1])
                self.add_metric('haproxy_%s_beconn_%s' % (name, 'avg'), float(sum(beconn)) / len(beconn))
                for code in self.response_codes:
                    self.add_metric('haproxy_%s_%s_hits' % (name, code), float(listener["responses"][code]) / check_time)


        for (name, val) in self.metricshash.iteritems():
            if 'hits_p' in name:
                results.append(GangliaMetricObject(name, val, units='percent'))
            elif 'hits' in name:
                results.append(GangliaMetricObject(name, val, units='hps'))
            elif 'latency' in name:
                results.append(GangliaMetricObject(name, val, units='sec'))
            else:
                results.append(GangliaMetricObject(name, val, units='connections'))

        # return a list of metric objects
        return results
