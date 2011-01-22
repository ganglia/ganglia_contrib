Name: Nagios alerter for Ganglia
Author: Vladimir Vuksan

Purpose of this script is to allow to alert on any Ganglia metric. Nice
plus with this set up is that you don't need to run NSCA. You already
have the metrics so why not use them.

You would use it by invoking the command then supply hostname you want
to alert on, metric and the critical condition ie. 

disk_free less 10

Meaning critical threshold has been reached if disk_free is less than 10 (GB).
Alternatively you can say

cpu_user more 80

meaning if the CPU user is greater than 80(%) that is critical.
 
I have it defined in Nagios this way

    define command{
        command_name    check_ganglia_metric
        command_line  	/opt/ganglia/check_ganglia_metric.php $HOSTADDRESS$ $ARG1$ $ARG2$ $ARG3$
        }


Then I simply add following definition

    define service{
        use				critical-service
        hostgroup_name			prod_hosts
        service_description             DISKFREE_ROOTFS
        check_command			check_ganglia_metric!disk_free_space_rootfs!less!4
        max_check_attempts         	4
        normal_check_interval         	5
        }


# Configuration

To configure in most cases you will only need to change the directory where your Ganglia
web is located ie.

$GANGLIA_WEB = "/var/www/html/ganglia";

Also you will need to decide whether you want to cache data or not and create the cache directory
ie.

install -o nagios -d /tmp/nagios
