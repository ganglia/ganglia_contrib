GMOND-DEBUG
===========

BUILDING
--------

```
. source.env
for i in gems/cache/*.gem; do gem install $i; done
```

RUNNING
-------

```
. source.env
./bin/gmond-debug
```


OLD DOCUMENTATION
-----------------

### What is this project about:

There is not one monitoring project to rule them all:

Ganglia, Graphite, Collectd, Opentsdb, ... they all have their specific unique functionality and their associate unique storage.

Instead of trying to create one central storage, we want to send the different metric information, to each monitoring solution for their optimized function.

This project's code will:

- listen into the gmond UDP protocol 
- optionally poll existing gmond's and put the message on to a 0mq (pub/sub).

From there, other subscribers can pull the information into graphite, collectd, opentsdb etc..

We have deliberately chosen not to go for peer to peer communication, but for a bus/queue oriented system.

It currently doesn't do more than put things on the queue, the next step is to write subscribers for the other monitoring systems.

And maybe , just maybe,  this will evolve into a swiss-army knife of monitoring/metrics conversion ....

### Thanks!

A big thanks to Vladimir Vuksan (@vvuksan) for helping me out with the original proof of concept!

### Requirements:
#### Centos

    # yum install libxml2-devel
    # yum install libxslt-devel
    # yum install zeromq-devel
    # yum install uuid-devel
    # yum install json-c-devel

### Configuring gmond

Just add another udp send channel for your existing gmond's

    udp_send_channel {
        host = 127.0.0.1
        port = 1234
    }

### Running it:

    gmond-zmq - A gmond UDP receiver that pushes things to a 0mq Pub/Sub

    Usage: gmond-zmq [-p port] [-P file] [-d] [-k]
    gmond-zmq --help

      -p, --port PORT           Specify port
    (default: 1234)
      -P, --pid FILE            save PID in FILE when using -d option.
    (default: /var/run/gmond-zmq.pid)
      -d, --daemon              Daemonize mode
      -k, --kill [PORT]         Kill specified running daemons - leave blank to kill all.
      -u, --user USER           User to run as
      -G, --group GROUP         Group to run as
      --gmond-host [HOST]   hostname/ip address of the gmond to poll
      --gmond-port [PORT]   tcp port of the gmond to poll
      --gmond-interval [seconds]
    interval to poll the gmond, 0 = disable (default)
      --zmq-port [PORT]     tcp port of the zmq publisher
      --zmq-host [HOST]     hostname/ip address of the zmq publisher
      -v, --verbose             more verbose output
      -t, --test-zmq            Starts a test zmq subscriber
      -?, --help                Display this usage information.

### Message examples

    {"timestamp":1324639623,"payload":{"name":"machine_type","val":"x86_64","slope":"zero","dmax":"0","tn":"809","units":"","type":"string","tmax":"1200","hostname":"localhost"},"id":"f6412a10-0f86-012f-0bdb-080027701f72","context":"METRIC","source":"GMOND"}
    {"timestamp":1324639623,"payload":{"name":"proc_total","val":"105","slope":"both","dmax":"0","tn":"89","units":" ","type":"uint32","tmax":"950","hostname":"localhost"},"id":"f6415250-0f86-012f-0bdc-080027701f72","context":"METRIC","source":"GMOND"}
    {"timestamp":1324639623,"payload":{"name":"cpu_num","val":"1","slope":"zero","dmax":"0","tn":"809","units":"CPUs","type":"uint16","tmax":"1200","hostname":"localhost"},"id":"f6417410-0f86-012f-0bdd-080027701f72","context":"METRIC","source":"GMOND"}
    {"timestamp":1324639623,"payload":{"name":"cpu_speed","val":"2800","slope":"zero","dmax":"0","tn":"809","units":"MHz","type":"uint32","tmax":"1200","hostname":"localhost"},"id":"f64186c0-0f86-012f-0bdf-080027701f72","context":"METRIC","source":"GMOND"}
    {"timestamp":1324639623,"payload":{"name":"pkts_out","val":"3.27","slope":"both","dmax":"0","tn":"49","units":"packets/sec","type":"float","tmax":"300","hostname":"localhost"},"id":"f641aa00-0f86-012f-0be0-080027701f72","context":"METRIC","source":"GMOND"}
    {"timestamp":1324639623,"payload":{"name":"swap_free","val":"741752","slope":"both","dmax":"0","tn":"89","units":"KB","type":"float","tmax":"180","hostname":"localhost"},"id":"f641c720-0f86-012f-0be1-080027701f72","context":"METRIC","source":"GMOND"}

### Some inspiration:

- [The Ganglia XDR protocol](https://github.com/fastly/ganglia/blob/master/lib/gm_protocol.x)
- [Gmetric library - ruby lib to send ganglia metrics](https://github.com/igrigorik/gmetric/blob/master/lib/gmetric.rb)
- [Gmond Source code](https://github.com/ganglia/monitor-core/blob/master/gmond/gmond.c#L1211)
- [Gmetric Python code](https://github.com/ganglia/ganglia_contrib/blob/master/gmetric-python/gmetric.py#L107)
- [Vladimir Vuksan sample Python Gmond Listener code](https://gist.github.com/1377993)
- [My initial sample Gmond listener code](https://gist.github.com/1376525)
- [Ruby XDR gem](http://rubyforge.org/projects/ruby-xdr/)
