====================
check_ganglia_metric
====================


Introduction
------------

**check_ganglia_metric** is a `Nagios <http://nagios.org/>`_ plugin that allows
you to trigger alerts on any Ganglia metric. This plugin was heavily inspired
by Vladimir Vuksan's check_ganglia_metric.php, but it comes with a number of
improvements.


Requirements
------------

#. Python >= 2.6
#. `NagAconda <http://pypi.python.org/pypi/NagAconda>`_ >= 0.1.4

To check which version of Python you have:

::

  python -V

To install NagAconda:

::

  pip install NagAconda

...or:

::

  easy_install NagAconda



Ganglia Configuration
---------------------

Unless your Nagios server and Ganglia Meta Daemon are running on the same host,
You probably need to edit your **gmetad.conf** to allow remote connections from
your Nagios server.

To allow connections from **nagios-server.example.com**:

::

  trusted_hosts nagios-server.example.com

To allow connections from **all hosts** (probably a security risk):

::

  all_trusted on


Testing on the Command Line
---------------------------

First, let's see if **check_ganglia_metric** can communicate with the Ganglia
Meta Daemon:

::

  $ check_ganglia_metric --gmetad_host=gmetad-server.example.com \
    --metric_host=host.example.com --metric_name=cpu_idle
  Status Ok, cpu_idle = 99.7|cpu_idle=99.7;;;;

The "Status Ok" message indicates that **check_ganglia_metric** is working. If
you're having trouble getting this to work, try again with verbose logging
enabled (``--verbose``) in order to gain better insight into what's going
wrong.

Now let's try setting an alert threshold:

::

  $ check_ganglia_metric --gmetad_host=gmetad-server.example.com \
    --metric_host=host.example.com --metric_name=cpu_idle --critical=99
  Status Critical, cpu_idle = 99.6|cpu_idle=99.6;;99;;

We told **check_ganglia_metric** to return a "Critical" status if the Idle CPU
was greater than 99. The "Status Critical" message indicates that it worked.
Note that **check_ganglia_metric** parses ranges and thresholds according to
the `official Nagios plugin development guidelines
<http://nagiosplug.sourceforge.net/developer-guidelines.html#THRESHOLDFORMAT>`_.

To see a complete list of command line options with brief explanations, run
**check_ganglia_metric** with the ``--help`` option.


Nagios Configuration
--------------------

First, create a command definition:

::

  define command {
    command_name  check_ganglia_metric
    command_line  /usr/lib/nagios/plugins/check_ganglia_metric --gmetad_host=gmetad-server.example.com --metric_host=$HOSTADDRESS$ --metric_name=$ARG1$ --warning=$ARG2$ --critical=$ARG3$
  }

Now you can use the above command in your service definitions:

::

  define service {
    service_description  CPU idle - Ganglia
    use                  some_template
    check_command        check_ganglia_metric!cpu_idle!0:20!0:0
    host_name            host.example.com
  }

Now we have a small problem in that if something goes wrong with
**check_ganglia_metric** (e.g. the cache file can't be read/written to, the
Ganglia Meta Daemon can't be reached, etc.), every service that relies on it
will fail, possibly inundating you with alerts. We can prevent this through the
use of service dependencies.

The first thing we need to do is create a command for checking the age of a
file:

::

  define command {
    command_name check_file_age
    command_line /usr/lib/nagios/plugins/check_file_age -f $ARG1$ -w $ARG2$ -c $ARG3$
  }

Next, we define a service which checks the age of **check_ganglia_metric**'s
cache file. Note that in order to be truly effective, this service needs to be
checked at least as (preferably more) frequently than all the other checks
that rely on **check_ganglia_metric**:

::

  define service {
    service_description           Cache for check_ganglia_metric
    use                           some_template
    check_command                 check_file_age!/var/lib/nagios/.check_ganglia_metric.cache!60!120
    host_name                     localhost
    check_interval                1
    max_check_attempts            1
  }

::

And finally, we set up the actual service dependency. Note that I've enabled
**use_regexp_matching** in Nagios, which allows me to use regular expressions
in my directives. By sticking "- Ganglia" at the end of every service that
relies on **check_ganglia_metric**, I can save myself a lot of effort:

::

  define servicedependency {
    host_name                     localhost
    service_description           check_ganglia_metric
    dependent_host_name           .*
    dependent_service_description .* \- Ganglia$
    execution_failure_criteria    c,p
  }

Now if something goes wrong with **check_ganglia_metric**, you'll get just one
alert about the cache file, and all dependent service checks will be paused
until you fix the problem that caused **check_ganglia_metric** to fail. Once
the problem is fixed, you'll need to update the timestamp on the cache file in
order to put the "Cache for check_ganglia_metric" service back into an OK state
(which will allow dependent service checks to continue):

::

  $ touch /var/lib/nagios/.check_ganglia_metric.cache


Tips and Tricks
---------------

It's possible to get a complete list of available hosts and metrics by enabling
"more verbose" logging (``-vv``). Since the metric_host and metric_name options
are required, you have a little bit of a "chicken and egg" problem here, but
that's OK. Just supply some dummy data. The plugin will error out at the end
with a "host/metric not found" error, but not before it dumps its cache:

::

  $ check_ganglia_metric --gmetad_host=gmetad-server.example.com \
    --metric_host=dummy --metric_name=dummy


Known Issues
------------

- Doesn't work with Python 2.4


Author
-------

Michael T. Conigliaro <mike [at] conigliaro [dot] org>
