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

#. Python >= 2.4
#. `NagAconda <http://pypi.python.org/pypi/NagAconda>`_ >= 0.1.4

To check which version of Python you have:

``python -V``

To install NagAconda:

``pip install NagAconda`` **or** ``easy_install NagAconda``


Ganglia Configuration
---------------------

Unless your Nagios server and Ganglia Meta Daemon are running on the same host,
You probably need to edit your **gmetad.conf** to allow remote connections from
your Nagios server.

To allow connections from **nagios-server.example.com**:

``trusted_hosts nagios-server.example.com``

To allow connections from **all hosts** (probably a security risk):

``all_trusted on``


Testing on the Command Line
---------------------------

First, let's see if the plugin can communicate with the Ganglia Meta Daemon:

::

  $ check_ganglia_metric --gmetad_host=gmetad-server.example.com \
    --metric_host=host.example.com \
    --metric_name=cpu_idle
  Status Ok, cpu_idle = 99.7|cpu_idle=99.7;;;;

The "Status Ok" message indicates that the plugin is working. If you're having
trouble getting this to work, try again with verbose logging enabled
(``-v`` or ``-vv``) in order to gain some insight into what's going wrong.

Now let's try setting an alert threshold:

::

  $ check_ganglia_metric --gmetad_host=gmetad-server.example.com \
    --metric_host=host.example.com \
    --metric_name=cpu_idle \
    --critical=99
  Status Critical, cpu_idle = 99.6|cpu_idle=99.6;;99;;

We told the plugin to return a "Critical" status if the Idle CPU was greater
than 99. The "Status Critical" message indicates that this worked. Note that
**check_ganglia_metric** parses ranges and thresholds according to the
`official Nagios plugin development guidelines <http://nagiosplug.sourceforge.net/developer-guidelines.html#THRESHOLDFORMAT>`_.

So what if you wanted to see a list of



**check_ganglia_metric** has many command line options. To see a complete list
with brief explanations, run the plugin with the ``--help`` option.


Nagios Configuration
--------------------

First create a command definition:

::

  define command {
    command_name  check_ganglia_metric
    command_line  /usr/lib/nagios/plugins/check_ganglia_metric --gmetad_host=gmetad-server.example.com --metric_host=$HOSTADDRESS$ --metric_name=$ARG1$ --warning=$ARG2$ --critical=$ARG3$
  }

Now you can use the above command in your service definitions:

::

  define service {
    service_description  CPU idle
    use                  my_template
    check_command        check_ganglia_metric!cpu_idle!0:20!0:0
    host_name            host.example.com
  }


Author
-------

Michael T. Conigliaro <mike [at] conigliaro [dot] org>