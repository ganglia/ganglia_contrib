#!/usr/bin/env python

import urllib2
import os.path
import os
import time

import rrdtool
from lxml import etree

def make_graph_load(dir, imgdir, host, duration, width='400'):
    """
    Specialized fform for Load Graphs
    """

    print "HOST = " + host
    # this oculd be imporved by just reusing the 1-m load
    # instead of using 1,5,15 metrics, but whatever
    
    f = host + '-load-' + str(duration) + '-' + str(width) + '.png' 
    imgfile = os.path.join(imgdir, f)

    # if less than X seconds old, just return imgfile
    
    load1_rrdfile = os.path.join(dir, host, "load_one.rrd")
    load5_rrdfile = os.path.join(dir, host, "load_five.rrd")
    load15_rrdfile = os.path.join(dir, host, "load_fifteen.rrd")
    
    rrdtool.graph(imgfile,
                  '--end', 'now',
                  '--start', 'end-' + str(duration),
                  '--width', str(width),
                  '--imgformat', 'PNG',
                  '--lower-limit', '0',
                  '--title', 'Load',
                  'DEF:l1=' + load1_rrdfile + ':load_one:AVERAGE',
                  'DEF:l5=' + load5_rrdfile + ':load_five:AVERAGE',
                  'DEF:l15=' + load15_rrdfile + ':load_fifteen:AVERAGE',
                  'AREA:l1#0000FF:load 1',
                  'LINE3:l1#000000',
                  'LINE3:l5#00FF00:load 5',
                  'LINE3:l15#FF0000:load 15'
                  )
    
    return imgfile

def make_graph_cpu(dir, imgdir, host, duration, width='400'):
    """
    Specialized form for CPU graphs
    """
    
    f = host + '-cpu-' + duration + '-' + str(width) + '.png' 
    imgfile = os.path.join(imgdir, f)
    
    sys_rrdfile = os.path.join(dir, host, "cpu_system.rrd")
    user_rrdfile = os.path.join(dir, host, "cpu_user.rrd")
    nice_rrdfile = os.path.join(dir, host,  "cpu_nice.rrd")
    
    rrdtool.graph(imgfile,
                  '--end', 'now',
                  '--start', 'end-' + duration,
                  '--width', str(width),
                  '--imgformat', 'PNG',
                  '--lower-limit', '0',
                  '--upper-limit', '100',
                  '--title', 'CPU Usage',
                  'DEF:sys=' + sys_rrdfile + ':cpu_system:AVERAGE',
                  'DEF:user=' + user_rrdfile + ':cpu_user:AVERAGE',
                  'DEF:nice=' + nice_rrdfile + ':cpu_nice:AVERAGE',
                  'AREA:sys#0000FF:"cpu system"',
                  'AREA:user#00FF00:"cpu user":STACK',
                  'AREA:nice#FF0000:"cpu nice":STACK'
                  )
    return imgfile

def make_graph_network(dir, imgdir, host, duration, width='400'):
    """
    Specialized form for network graphs
    """
    
    f = host + '-network-' + duration + '-' + str(width) + '.png' 
    imgfile = os.path.join(imgdir, f)
    
    bytesin_rrdfile = os.path.join(dir, host, "bytes_in.rrd")
    bytesout_rrdfile = os.path.join(dir, host,  "bytes_out.rrd")
    print bytesin_rrdfile
    
    rrdtool.graph(imgfile,
                  '--end', 'now',
                  '--start', 'end-' + duration,
                  '--width', str(width),
                  '--imgformat', 'PNG',
                  '--lower-limit', '0',
                  '--title', 'Network Bytes',
                  'DEF:bi=' + bytesin_rrdfile + ':bytes_in:AVERAGE',
                  'DEF:bo=' + bytesout_rrdfile + ':bytes_out:AVERAGE',
                  'LINE1:bi#0000FF:bytes in',
                  'LINE1:bo#FF0000:bytes out'
                  )
    return imgfile

def make_graph_memory(dir, imgdir, host, duration, width='400'):
    """
    Specialized form for CPU graphs
    """
    
    f = host + '-memory-' + duration + '-' + str(width) + '.png' 
    imgfile = os.path.join(imgdir, f)
    
    mem_rrdfile = os.path.join(dir, host, "mem_used_percent.rrd")
    swap_rrdfile = os.path.join(dir, host, "swap_used_percent.rrd")
    disk_rrdfile = os.path.join(dir, host, "disk_used_percent.rrd")
    
    rrdtool.graph(imgfile,
                  '--end', 'now',
                  '--start', 'end-' + duration,
                  '--width', str(width),
                  '--imgformat', 'PNG',
                  '--lower-limit', '0',
                  '--upper-limit', '100',
                  
                  '--title', '% of Memory,Swap,Disk Used',
                  'DEF:bi=' + mem_rrdfile + ':mem_used_percent:AVERAGE',
                  'DEF:bo=' + swap_rrdfile + ':swap_used_percent:AVERAGE',
                  'DEF:disk=' + disk_rrdfile + ':disk_used_percent:AVERAGE',
                  'LINE1:bi#0000FF:memory used',
                  'LINE1:bo#FF0000:swap used',
                  'LINE1:disk#00FF00:disk used'
                  )
    return imgfile

def make_graph(dir, imgdir, host, metric, duration, width='400'):
    #--end now --start end-120000s --width 400
    
    if metric == 'cpu':
        return make_graph_cpu(dir,imgdir,host,duration,width)
    if metric == 'network':
        return make_graph_network(dir,imgdir,host,duration,width)
    if metric == 'memory':
        return make_graph_memory(dir,imgdir,host,duration,width)
    if metric == 'load':
        return make_graph_load(dir,imgdir,host,duration,width)
    
    f = str(host) + '-' + metric + '-' + str(duration) + '-' + str(width) + '.png'
    
    imgfile = os.path.join(imgdir, f)
    rrdfile = os.path.join(dir,  host, metric + ".rrd")
    print rrdfile
    rrdtool.graph(imgfile,
                  '--end', 'now',
                  '--start', 'end-' + duration,
                  '--width', '400',
                  '--imgformat', 'PNG',
                  '--title', metric,
                  'DEF:ds0a=' + rrdfile + ':' + metric + ':AVERAGE',
                  'LINE1:ds0a#0000FF:"default resolution\l"'
                  )
    return imgfile

if __name__ == '__main__':

    host = '172.16.70.128'
    rrddir = '/tmp'
    imgdir = '/tmp'
    
    make_graph(rrddir, imgdir, host, 'cpu_idle', '300s')
    make_graph_cpu(rrddir, imgdir, host, '300s')
    make_graph_load(rrddir, imgdir, host, '300s')
    make_graph_network(rrddir, imgdir, host, '300s')
    make_graph_memory(rrddir, imgdir, host, '300s')

    
