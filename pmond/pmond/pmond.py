#!/usr/bin/env python

# This is the MIT License
# http://www.opensource.org/licenses/mit-license.php
#
# Copyright (c) 2007,2008 Nick Galbreath
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
from gmetric import Gmetric
import metric
import logging
from os import uname
ostype = uname()[0]
if ostype == 'Linux':
    from metrics_linux import *
elif ostype == 'Darwin':
    from metrics_darwin import *
else:
    print "whoops"
    sys.exit(1)

keep_processing = True

class consumer(object):
    """
    collection of "metric collectors"
    """
    def __init__(self):
        self.ary = []
    def addMetric(self, values, host=None):
        for a in self.ary:
            a.addMetric(values, host)
    def addConsumer(self, o):
        self.ary.append(o)

class emitter(object):
    """
    A consumer of metrics that sends via gmetric
    """
    def __init__(self, host, port, protocol):
        self.g = Gmetric(host, port, protocol)

    def addMetric(self, values, host=None):
        logging.debug("sending %s = %s", values['NAME'], values['VAL'])
        logging.debug("DICT = %s", str(values))
        self.g.send(values['NAME'], values['VAL'],  values['TYPE'],
                    values['UNITS'], values['SLOPE'], values['TMAX'],
                    values['DMAX'])

from subprocess import Popen, PIPE
import sched
from time import time, sleep
import sys
import socket

from collections import defaultdict
from gmetric import gmetric_read
from socket import gethostname


class monitortree(object):
    """
    A consumer of metrics that stores things in a xml tree
    """
    def __init__(self):
        self.hosts = defaultdict(dict)
        self.hostname = gethostname()

    def addMetric(self, values, host=None):
        # HOST -> METRICS -> VALUES

        # add timestamp to figureout node expiration
        values['_now'] = time()

        # TBD: replace with defaultdict
        if host is None:
            host = self.hostname

        metrics = self.hosts[host]
        name = values['NAME']
        metrics[name] = values

    def xml(self):
        parts = []

        # TBD: look at Ganglia 3
        parts.append('<GANGLIA_XML VERSION="2.5.7" SOURCE="gmond">\n')
        for host,metrics in self.hosts.iteritems():
            parts.append('<HOST name="%s">\n' % host)
            zap = []
            for name, values in metrics.iteritems():

                # figure out if this node "expired"
                expires = 0
                if '_now' in values and 'TMAX' in values:
                    now = time()
                    tmax = float(values['TMAX'])
                    if tmax > 0:
                        expires = float(values['_now']) + float(values['TMAX'])
                if expires and expires < now:
                    zap.append(values['NAME'])
                    continue
                
                # print the node
                parts.append('<METRIC NAME="' + values['NAME'] + '"')
                for k,v in values.iteritems():
                    if k != '_now' and k != 'NAME':
                        parts.append(' ' + k + '="' + str(v) + '"')
                parts.append('/>\n')

            # delete the expired nodes
            for name in zap:
                del metrics[name]

            parts.append('\n</HOST>\n')
        parts.append('</GANGLIA_XML>\n')
        return ''.join(parts)


# THREE THREADS
#  * writers
#  * receiver
#  * monitor
#
#
import threading
class Monitor(threading.Thread):
    def __init__(self, tree):
        threading.Thread.__init__(self)
        self.tree = tree

    def run(self):
        # MACHINE 
        s = sched.scheduler(time, sleep)

        for m in [metric_cpu(),
                  metric_iostat(),
                  metric_mem(),
                  metric_disk(),
                  metric_proc(),
                  metric_sys_clock(),
                  metric_net() ]:
            m.register(s, self.tree)

        s.run()

class Reader(threading.Thread):
    """
    Accepts UDP XDR gmetric packets
    """
    def __init__(self, tree):
        threading.Thread.__init__(self)
        self.tree = tree

    def run(self):
        tree = self.tree

        serversocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        serversocket.bind(('', 4001))
        #serversocket.listen(5)
        serversocket.setblocking(1)
        serversocket.settimeout(None)
        while keep_processing:
            try:
                print "loop"
                data, address = serversocket.recvfrom(512)
                tree.addMetric(gmetric_read(data))
            except KeyboardInterrupt:
                print "got intertupe"
            except socket.timeout:
                print "udp timeout"
                
class Writer(threading.Thread):
    """
    Writes out metrics tree as XML
    """
    def __init__(self, tree):
        threading.Thread.__init__(self)
        self.tree = tree

    def run(self):
        serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serversocket.settimeout(None)
        serversocket.bind(('', 4000))
        serversocket.listen(5)
        while keep_processing:
            try:
                clientsocket, address = serversocket.accept()
                clientsocket.send(self.tree.xml())
                clientsocket.close()
            except KeyboardInterrupt:
                print "got intertupe"

            except socket.timeout:
                print "got timeout"

def main():

    tree =  monitortree()

    r = Reader(tree)
    w = Writer(tree)

    c = consumer()
    e = emitter('172.16.70.128', 8649, 'udp')
    c.addConsumer(e)
    c.addConsumer(tree)

    m = Monitor(c)
    r.start()
    w.start()
    m.start()


    m.join()

    while m.isAlive():
        try:
            m.join(1000)
        except KeyboardInterrupt:
            print "Exit on main"
            sys.exit(1)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    #from daemon import *
    #drop_privileges()
    #daemonize()
    main()
