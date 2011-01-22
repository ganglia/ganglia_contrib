# This example cron job gathers metrics using DummyLogtailer every 5 minutes and
# submits them to gmetric.  DummyLogtailer is an example plugin that just counts
# the number of lines logged per second.

*/5 * * * * root /usr/bin/ganglia-logtailer --classname DummyLogtailer --log-file /var/log/mail.log --mode cron

