#
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

import os
import sys

#http://www.noah.org/wiki/Daemonize_Python
def daemonize (stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
  
    # Do first fork.
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)   # Exit first parent.
    except OSError, e:
        sys.stderr.write ("fork #1 failed: (%d) %s\n" % (e.errno, e.strerror) )
        sys.exit(1)
 
    # Decouple from parent environment.
    os.chdir("/")
    os.umask(0)
    os.setsid()
 
    # Do second fork.
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)   # Exit second parent.
    except OSError, e:
        sys.stderr.write ("fork #2 failed: (%d) %s\n" % (e.errno, e.strerror) )
        sys.exit(1)
 
    # Now I am a daemon!
 
    # Redirect standard file descriptors.
    si = open(stdin, 'r')
    so = open(stdout, 'a+')
    se = open(stderr, 'a+', 0)
    os.dup2(si.fileno(), sys.stdin.fileno())
    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(se.fileno(), sys.stderr.fileno())


def drop_privileges(uid_name='nobody', gid_name='nogroup'):
    import pwd, grp

    starting_uid = os.getuid()
    starting_gid = os.getgid()

    starting_uid_name = pwd.getpwuid(starting_uid)[0]

    if os.getuid() != 0:
        # We're not root so, like, whatever dude
        return

    if starting_uid == 0:

        # Get the uid/gid from the name
        running_uid = pwd.getpwnam(uid_name)[2]
        #running_gid = grp.getgrnam(gid_name)[2]

        # Try setting the new uid/gid
        #os.setgid(running_gid)
        os.setuid(running_uid)

        new_umask = 077
        old_umask = os.umask(new_umask)
        sys.stderr.write('drop_privileges: Old umask: %s, new umask: %s\n' % \
                             (oct(old_umask), oct(new_umask)))
        
    final_uid = os.getuid()
    final_gid = os.getgid()
    sys.stderr.write('drop_privileges: running as %s/%s\n' % \
                         (pwd.getpwuid(final_uid)[0],
                          grp.getgrgid(final_gid)[0]))

