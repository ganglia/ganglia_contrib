#!/usr/bin/ruby

# this script reports some statistics about how nagios is functioning to ganglia
# put all the checks you want reported in the $checks hash and they'll get included
# it reports metrics every 15s and is intended to be called from cron every 1m

# possible metrics:
# PROGRUNTIME          string with time Nagios process has been running.
# PROGRUNTIMETT        time Nagios process has been running (time_t format).
# STATUSFILEAGE        string with age of status data file.
# STATUSFILEAGETT      string with age of status data file (time_t format).
# NAGIOSVERSION        string with Nagios version.
# NAGIOSPID            pid number of Nagios deamon.
# NAGIOSVERPID         string with Nagios version and PID.
# TOTCMDBUF            total number of external command buffer slots available.
# USEDCMDBUF           number of external command buffer slots currently in use.
# HIGHCMDBUF           highest number of external command buffer slots ever in use.
# NUMSERVICES          total number of services.
# NUMHOSTS             total number of hosts.
# NUMSVCOK             number of services OK.
# NUMSVCWARN           number of services WARNING.
# NUMSVCUNKN           number of services UNKNOWN.
# NUMSVCCRIT           number of services CRITICAL.
# NUMSVCPROB           number of service problems (WARNING, UNKNOWN or CRITIAL).
# NUMSVCCHECKED        number of services that have been checked since start.
# NUMSVCSCHEDULED      number of services that are currently scheduled to be checked.
# NUMSVCFLAPPING       number of services that are currently flapping.
# NUMSVCDOWNTIME       number of services that are currently in downtime.
# NUMHSTUP             number of hosts UP.
# NUMHSTDOWN           number of hosts DOWN.
# NUMHSTUNR            number of hosts UNREACHABLE.
# NUMHSTPROB           number of host problems (DOWN or UNREACHABLE).
# NUMHSTCHECKED        number of hosts that have been checked since start.
# NUMHSTSCHEDULED      number of hosts that are currently scheduled to be checked.
# NUMHSTFLAPPING       number of hosts that are currently flapping.
# NUMHSTDOWNTIME       number of hosts that are currently in downtime.
# NUMHSTACTCHKxM       number of hosts actively checked in last 1/5/15/60 minutes.
# NUMHSTPSVCHKxM       number of hosts passively checked in last 1/5/15/60 minutes.
# NUMSVCACTCHKxM       number of services actively checked in last 1/5/15/60 minutes.
# NUMSVCPSVCHKxM       number of services passively checked in last 1/5/15/60 minutes.
# xxxACTSVCLAT         MIN/MAX/AVG active service check latency (ms).
# xxxACTSVCEXT         MIN/MAX/AVG active service check execution time (ms).
# xxxACTSVCPSC         MIN/MAX/AVG active service check % state change.
# xxxPSVSVCLAT         MIN/MAX/AVG passive service check latency (ms).
# xxxPSVSVCPSC         MIN/MAX/AVG passive service check % state change.
# xxxSVCPSC            MIN/MAX/AVG service check % state change.
# xxxACTHSTLAT         MIN/MAX/AVG active host check latency (ms).
# xxxACTHSTEXT         MIN/MAX/AVG active host check execution time (ms).
# xxxACTHSTPSC         MIN/MAX/AVG active host check % state change.
# xxxPSVHSTLAT         MIN/MAX/AVG passive host check latency (ms).
# xxxPSVHSTPSC         MIN/MAX/AVG passive host check % state change.
# xxxHSTPSC            MIN/MAX/AVG host check % state change.
# NUMACTHSTCHECKSxM    number of total active host checks occuring in last 1/5/15 minutes.
# NUMOACTHSTCHECKSxM   number of on-demand active host checks occuring in last 1/5/15 minutes.
# NUMCACHEDHSTCHECKSxM number of cached host checks occuring in last 1/5/15 minutes.
# NUMSACTHSTCHECKSxM   number of scheduled active host checks occuring in last 1/5/15 minutes.
# NUMPARHSTCHECKSxM    number of parallel host checks occuring in last 1/5/15 minutes.
# NUMSERHSTCHECKSxM    number of serial host checks occuring in last 1/5/15 minutes.
# NUMPSVHSTCHECKSxM    number of passive host checks occuring in last 1/5/15 minutes.
# NUMACTSVCCHECKSxM    number of total active service checks occuring in last 1/5/15 minutes.
# NUMOACTSVCCHECKSxM   number of on-demand active service checks occuring in last 1/5/15 minutes.
# NUMCACHEDSVCCHECKSxM number of cached service checks occuring in last 1/5/15 minutes.
# NUMSACTSVCCHECKSxM   number of scheduled active service checks occuring in last 1/5/15 minutes.
# NUMPSVSVCCHECKSxM    number of passive service checks occuring in last 1/5/15 minutes.
# NUMEXTCMDSxM         number of external commands processed in last 1/5/15 minutes.

# methods by which we munge the value returned by nagios3stats
donothing = lambda {|val| val}
ms2sec = lambda {|val| val.to_f / 1000}
# hash translating MRTG name listed (from above) to the stuff that ganglia needs to know.
$checks = {
	"NUMSERVICES"     => {"name" => "total_num_services", "type" => "int32", "units" => "services", "transformation" => donothing},
	"NUMHOSTS"        => {"name" => "total_num_hosts", "type" => "int32", "units" => "hosts", "transformation" => donothing},
	"NUMSVCOK"        => {"name" => "num_services_ok", "type" => "int32", "units" => "services", "transformation" => donothing},
	"NUMSVCWARN"      => {"name" => "num_services_warn", "type" => "int32", "units" => "services", "transformation" => donothing},
	"NUMSVCUNKN"      => {"name" => "num_services_unknown", "type" => "int32", "units" => "services", "transformation" => donothing},
	"NUMSVCCRIT"      => {"name" => "num_services_crit", "type" => "int32", "units" => "services", "transformation" => donothing},
	"NUMSVCPROB"      => {"name" => "num_services_problem", "type" => "int32", "units" => "services", "transformation" => donothing},
	"NUMHSTACTCHK1M"  => {"name" => "num_hosts_checked_1m", "type" => "int32", "units" => "hosts", "transformation" => donothing},
	"NUMHSTACTCHK5M"  => {"name" => "num_hosts_checked_5m", "type" => "int32", "units" => "hosts", "transformation" => donothing},
	"NUMHSTACTCHK15M" => {"name" => "num_hosts_checked_15m", "type" => "int32", "units" => "hosts", "transformation" => donothing},
	"NUMSVCACTCHK1M"  => {"name" => "num_services_checked_1m", "type" => "int32", "units" => "services", "transformation" => donothing},
	"NUMSVCACTCHK5M"  => {"name" => "num_services_checked_5m", "type" => "int32", "units" => "services", "transformation" => donothing},
	"NUMSVCACTCHK15M" => {"name" => "num_services_checked_15m", "type" => "int32", "units" => "services", "transformation" => donothing},
	"MINACTSVCLAT"    => {"name" => "service_check_latency_min", "type" => "float", "units" => "sec", "transformation" => ms2sec},
	"MAXACTSVCLAT"    => {"name" => "service_check_latency_max", "type" => "float", "units" => "sec", "transformation" => ms2sec},
	"AVGACTSVCLAT"    => {"name" => "service_check_latency_avg", "type" => "float", "units" => "sec", "transformation" => ms2sec},
	"MINACTSVCEXT"    => {"name" => "service_check_exec_time_min", "type" => "float", "units" => "sec", "transformation" => ms2sec},
	"MAXACTSVCEXT"    => {"name" => "service_check_exec_time_max", "type" => "float", "units" => "sec", "transformation" => ms2sec},
	"AVGACTSVCEXT"    => {"name" => "service_check_exec_time_avg", "type" => "float", "units" => "sec", "transformation" => ms2sec},
	"MINACTHSTLAT"    => {"name" => "host_check_latency_min", "type" => "float", "units" => "sec", "transformation" => ms2sec},
	"MAXACTHSTLAT"    => {"name" => "host_check_latency_max", "type" => "float", "units" => "sec", "transformation" => ms2sec},
	"AVGACTHSTLAT"    => {"name" => "host_check_latency_avg", "type" => "float", "units" => "sec", "transformation" => ms2sec},
	"MINACTHSTEXT"    => {"name" => "host_check_exec_time_min", "type" => "float", "units" => "sec", "transformation" => ms2sec},
	"MAXACTHSTEXT"    => {"name" => "host_check_exec_time_max", "type" => "float", "units" => "sec", "transformation" => ms2sec},
	"AVGACTHSTEXT"    => {"name" => "host_check_exec_time_avg", "type" => "float", "units" => "sec", "transformation" => ms2sec},
}
$myhostname = %x{hostname}.strip

def report_metrics()
	# get the stats as a newline separated list of numbers
	result = %x{/usr/sbin/nagios3stats -m -d #{$checks.keys.sort.join(',')}}

	# this little bit of magic makes a new hash out of the two arrays of sorted keys and results
	results = Hash[$checks.keys.sort.zip result.split]

	results.each_pair do |m, v|
		# munge the value if necessary (eg convert millisec to seconds)
		val = $checks[m]["transformation"].call v
		command_parts = [
			"/usr/bin/gmetric",
			"--name #{$checks[m]["name"]}",
			"--value #{val}",
			"--type #{$checks[m]["type"]}",
			"--units #{$checks[m]["units"]}",
			"--group nagios",
			"--spoof #{$myhostname}:#{$myhostname}",
		]
		%x{#{command_parts.join(' ')}}
	end
end

# report the metrics 4 times throughout the next 60s: 0s, 15s, 30s, and 45s then exit.
report_metrics
3.times do
	sleep 15
	report_metrics
end