#!/usr/bin/env python

# This is the MIT License
# http://www.opensource.org/licenses/mit-license.php
#
# Copyright (c) 2009 Nick Galbreath
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

import socket
from lxml import etree

def parse(s):
    hosts = {}
    root = etree.XML(s)
    # newer versions could do:
    #for host in root.iter('HOST'):    
    for host in root.findall('HOST'):
        name = host.get('NAME')
        hosts[name] = {}
        metrics = hosts[name]
        # new versions of lxml could do
        #for m in host.iter('METRIC'):
        for m in host.findall('METRIC'):
            metrics[m.get('NAME')] = m.attrib.get("VAL")
    return hosts
        
def read(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    data = ""
    while True:
        bytes = s.recv(4096)
        if len(bytes) == 0:
            break;
        data += bytes
    s.close()
    return data

if __name__ == '__main__':

    s = read('localhost', 8649)
    hosts = parse(s)
    for h in hosts:
        print h
        keys = sorted(hosts[h])
        for k in keys:
            print "   %s = %s" % (k,hosts[h][k])
            

