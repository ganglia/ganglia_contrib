#!/usr/bin/env python

import psyco
psyco.full()

from gmetric import Gmetric

if __name__ == '__main__':
    g = Gmetric('localhost', 4001, 'udp')
    for i in xrange(100000):
        g.send('foo', 'bar')
