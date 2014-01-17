#!/usr/bin/python

import sys
import syslog
import os
import urllib
import urllib2
import base64

########################################################################
# Make sure you change base Ganglia URL
########################################################################
ganglia_events_url = "<%= @ganglia_base_url %>/api/events.php"

# Optionally set user name and password
#username = "<%= @username %>"
#password = "<%= @password %>"

if (len(sys.argv) == 1):
  print "\nPlease supply a log message. It can be any number of arguments. Exiting....\n"
  exit(1)

for index in range(1,len(sys.argv)):
    print sys.argv[index]

# Log to syslog
syslog.syslog(" ".join(sys.argv))

# Remove first argument and join the list of arguments so it can be sent
summary = " ".join(sys.argv[1:])

# Get hostname
uname=os.uname()
hostname=uname[1]

params = urllib.urlencode({'action': 'add', 'start_time': 'now',
    'host_regex': hostname, 'summary': summary})

request = urllib2.Request(ganglia_events_url+ "?%s" % params)

if 'username' in locals():
  base64string = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')
  request.add_header("Authorization", "Basic %s" % base64string)   

f = urllib2.urlopen(request)

print f.read()