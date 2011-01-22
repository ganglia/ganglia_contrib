Name: Nagios alerter for Ganglia

Author: Vladimir Vuksan

Purpose of this script is to allow you to alert on any Ganglia metric. 
You could even do away with NSCA :-). You have already collected the
metrics so why not use them.

# Usage 

Run it with

check_ganglia_metric.php <hostname> <metric> <less|more|equal|notequal> <critical_value> ie.

e.g.

> php check_ganglia_metrics.php web15 disk_free less 10

You should get 

disk_free CRITICAL - Value = 0.317 GB

Meaning critical threshold has been reached if disk_free is less than 10 (GB).

Alternatively you can say

cpu_user more 80

meaning if the CPU user is greater than 80(%) that is critical.
 
# Nagios Usage

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


# Errors

If you get following error when running it by hand

PHP Warning:  include_once(./version.php): failed to open stream: No such file or directory in /var/www/html/ganglia/conf.php on line 6

PHP Warning:  include_once(): Failed opening './version.php' for inclusion (include_path='.:/usr/share/pear:/usr/share/php') in /var/www/html/ganglia/conf.php on line 6

You will need to put in the full path to version.php in /var/www/html/ganglia.php. Look for the
include that includes version.php


# More

More indepth instructions can be found here

[http://vuksan.com/linux/nagios_scripts.html#check_ganglia_metrics]
