#!/usr/bin/env python

# SYSTEM
import urllib2
import os.path
import os
import time
import sys
import logging    

# 3RD PARTY
import rrdtool
from lxml import etree

# LOCAL
import gparse

def rrd_update(rrdfile, name, value, slope):

    # fix annoying unicode issues
    rrdfile = str(rrdfile)
    
    dstype = 'GAUGE'
    if slope == 'zero':
        dstype = 'ABSOLUTE'
        # for now don't care about invariants
        return
    elif slope == 'both':
        dstype = 'GAUGE'
    elif slope == 'positive':
        dstype = 'COUNTER'
        
    token = 'DS:' + name + ':' + dstype + ':60:U:U'
    if not os.path.exists(rrdfile):
        logging.info("Creating %s\n", rrdfile)
        # 1440 is minutes per day
        # 300 minutes = 5 hours
        # 30 hours = 1800 minutes
        rrdtool.create(rrdfile, '--step=20', token,
                       # 1 point at 20s, 900 of them 300m, 5 hours
                       'RRA:AVERAGE:0.5:1:900',
                       # 3 points @ 20s = 60s = 1m, 30 hours
                       'RRA:AVERAGE:0.5:3:1800'
                       )
        # no else
    svalue = str(value)
    logging.debug("Updating '%s' with value of '%s'", rrdfile, svalue)
    rrdtool.update(rrdfile, 'N:' + svalue)

def make_standard_rrds(hosts, dir):
    """
    walks the host mappings and makes
    specialized graphs for various metrics
    """
    for host, metrics in hosts.iteritems():
        path = os.path.join(dir, host)
        if not os.path.isdir(path):
            os.mkdir(path)

        for mname, val in metrics.iteritems():
            # stuff we don't care about
            if mname in ('boottime', 'gexec', 'machine_type', 'os_name',
                         'os_release'):
                continue
            if mname.startswith('multicpu_') or mname.startswith('pkts_'):
                continue

            # these are handled differently
            if mname.startswith('mem_') or \
                   mname.startswith('swap_') or \
                   mname.startswith('disk_'):
                continue
            
            rrdfile = os.path.join(path, mname + ".rrd")
            #print "Adding %s = %s" % (mname, val)
            rrd_update(rrdfile, mname, val, 'both')

        # gmond reports "total" and "used" (absolute numbers)
        #   making rrds of both isn't very useful
        # so I merge them and make a consolidated version
        # of "% of total used" which is normally more interesting
            
        mem_total = float(metrics['mem_total'])
        mem_free = float(metrics['mem_free'])
        name = 'mem_used_percent'
        rrdfile = os.path.join(path, name + ".rrd")
        rrd_update(rrdfile, name, 100.0 *
                   (1.0 - mem_free / mem_total), 'both')
        
        swap_total = float(metrics['swap_total'])
        swap_free  = float(metrics['swap_free'])
        name = 'swap_used_percent'
        rrdfile = os.path.join(path, name + ".rrd")
        rrd_update(rrdfile, name, 100.0 *
                   (1.0 - swap_free / swap_total), 'both')
        
        disk_total = float(metrics['disk_total'])
        disk_free  = float(metrics['disk_free'])
        name = 'disk_used_percent'
        rrdfile = os.path.join(path, name + ".rrd")
        rrd_update(rrdfile, name, 100.0 *
                   (1.0 - disk_free / disk_total), 'both')


if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("", "--host", dest="host",
                      help="host", default="localhost");    
    parser.add_option("-p", "--port", dest="port",
                      help="port", default=8649);
    parser.add_option("-d", "--dir", dest="dir", default='/tmp',
                      help="directory to write RRD files")
    parser.add_option("-s", "--sleep", dest="sleep", default=20,
                      help="seconds to sleep between intervals")
    parser.add_option("-l", "--log", dest="log", default='warning',
                      help="log level: [ debug | info | warn | error ]")
    options, args = parser.parse_args()

    host = options.host
    port = int(options.port)
    dir = options.dir
    sleep = int(options.sleep)
    log = options.log.lower()
    if log == 'debug':
        loglevel = logging.DEBUG
    elif log == 'info':
        loglevel = logging.INFO
    elif log == 'warn' or log == 'warning':
        loglevel = logging.WARNING
    elif log == 'err' or log == 'error':
        loglevel = logging.ERROR

    logging.basicConfig(level=loglevel)
    
    logging.info("Using %s:%d and directory %s" % (host,port,dir))

    # now do checks

    # is dir a directory
    if not os.path.isdir(dir):
        logging.error("Directory '%s' does not exist. Exiting", dir)
        sys.exit(1)

    # can we write to it?
    # this is the LAME way of doing this
    try:
        tmpfile = os.path.join(dir, 'tmp')
        f = open(tmpfile, 'w')
        f.close()
        os.remove(tmpfile)
    except:
        logging.error("Directory '%s' is not writable. Exiting", dir)
        sys.exit(1)
        
    try:
        xml = gparse.read(host, port)
    except Exception,e:
        logging.error("Read of %s:%d failed -- is gmond running?  Exiting",
                      host, port)
        sys.exit(1)

    while True:
        try:
            logging.debug("Reading from %s:%d", host, port)
            t0 = time.time()
            xml = gparse.read(host, port)
            secs = time.time() - t0;
            logging.debug("Reading took %fs", secs)
            logging.debug("Parsing XML")
            t0 = time.time()
            hosts = gparse.parse(xml)
            secs = time.time() - t0;
            logging.debug("Parsing took %fs", secs)

            logging.debug("Inserting...")
            t0 = time.time()
            make_standard_rrds(hosts, dir)
            secs = time.time() - t0;
            logging.debug("Inserts took %fs", secs)
        except Exception,e:
            logging.error("Exception!: %s", str(e))

        logging.debug("Sleeping for %ds....\n", sleep)
        time.sleep(sleep)

