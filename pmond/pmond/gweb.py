#!/usr/bin/env python

#
# SUPER LOW LEVEL WEBSERVER
# Sorta like CGI if anyone remembers that
#
#
from wsgiref.simple_server import make_server
from wsgiref.util import FileWrapper
from wsgiref.util import shift_path_info
import cgi
import mimetypes
import os.path
import glob
import os.path
import gparse
import ggraph

static_root = '.'
rrd_root = '/tmp'
img_root = '/tmp'

def sendfile(fname, start_response):
    status =  "200 OK"
    mtype = 'text/plain'
    try:
        f = open(fname, 'r'); data = f.read(); f.close()
        m = mimetypes.guess_type(fname)
        if m[0] is not None: mtype = m[0]
    except IOError,e:
        data = str(e) + '\n'
        status = "404 Not Found"
    start_response(status, [('Content-Type', mtype)])
    return [ data ]

def static(environ, start_response):
    # shift PATH_INFO /static/foo ----> /foo
    # then skip first '/'
    # and merge with static_root
    shift_path_info(environ)
    filename = os.path.abspath(os.path.join(static_root,
                                            environ['PATH_INFO'][1:]))
    return sendfile(fname, start_response)

def overview(environ, start_response):
    qs = cgi.parse_qs(environ['QUERY_STRING'])
    host     = qs['host'][0]
    duration = qs['duration'][0]
    width    = qs['width'][0]
    status = '200 OK'
    headers = [('Content-type', 'text/html')]
    start_response(status, headers)
    html = ["<html><head><title>%s</title></head><body><ul>" % host]
    for metric in ('cpu', 'memory', 'load', 'network'):
        html.append('<img src="/rrd?host=%s&metric=%s&duration=%s&width=%s" />' % (host, metric, duration, width))
    html.append("</body></html>")
    return html

def hostlist(environ, start_response):
    # just get everyfile underneath 'rrd_root' and see
    #   if they are a directorya
    hosts = []
    files = glob.glob(rrd_root + '/*')
    for f in files:
        if os.path.isdir(f):
            hosts.append(os.path.basename(f))
    status = '200 OK'
    headers = [('Content-type', 'text/html')]
    start_response(status, headers)
    html = ["<html><head><title>HOSTS</title></head><body><ul>"]
    for h in hosts:
        html.append('<li><a href="/overview?host=%s&width=400&duration=1800s">%s</a></li>\n' % (h,h))
    html.append("""</ul></body></html>""")
    return html
    
def rrd(environ, start_response):
    shift_path_info(environ)
    filename = os.path.abspath(os.path.join(static_root,
                                            environ['PATH_INFO'][1:]))
    qs = cgi.parse_qs(environ['QUERY_STRING'])
    host = qs['host'][0]
    metric = qs['metric'][0]
    duration = qs['duration'][0]
    
    # optional
    width = 400
    if 'width' in qs:
        width = int(qs['width'][0])

    fname = ggraph.make_graph(rrd_root, img_root, host, metric, duration, width)
    
    return sendfile(fname, start_response)

# just for debugging
def echo(environ, start_response):
    status = '200 OK'
    headers = [('Content-type', 'text/plain')]
    start_response(status, headers)
    text = []
    keys = sorted(environ.keys())
    for k in keys:
        text.append("%s = %s\n" % (k,environ[k]))
    return text

def dispatch(environ, start_response):
    path = environ['PATH_INFO']
    if path == '/':
        return hostlist(environ, start_response)
    if path == '/overview':
        return overview(environ, start_response)
    if path == '/echo':
        return echo(environ, start_response)
    if path == '/rrd':
        return rrd(environ, start_response)

    # remap common webby things into the static directory
    if path == '/favicon.txt' or path == '/robots.txt':
        path = '/static' + path
        environ['PATH_INFO'] = path
    if path.startswith('/static'):
        return static(environ, start_response)

    # nothing matched, do 404
    status = "404 Not Found"
    start_response(status, [('Content-Type', 'text/plain')])
    return [ "%s not found" % path ]


if __name__ == '__main__':
    httpd = make_server('', 8000, dispatch)
    print "Serving on port 8000..."

    # Serve until process is killed
    httpd.serve_forever()
