Ganglia statistics for nagios

This script should be called from cron once per minute. It queries nagios for statistics about its process (eg number of checks, average check delay, number of warning / critical problems, etc.) and reports them to ganglia every 15 seconds.

Note that this is not a script to check ganglia metrics from nagios; for that go to https://github.com/ganglia/monitor-core/wiki/Integrating-Ganglia-with-Nagios

