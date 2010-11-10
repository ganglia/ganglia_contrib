#!/bin/sh

# clean up old backups
#find /var/lib/ganglia/ -name "rrds.bak_*" -mtime +7 -prune -exec rm -rf {} \;
# lets test this with an ls, shall we?  :)
#find /var/lib/ganglia/ -name "rrds.bak_*" -mtime +7 -prune -exec ls -ld {} \; -exec rm -rf {} \;
# ok, the test passed and it looks good.  Delete silently.
#find /var/lib/ganglia/ -name "rrds.bak_*" -mtime +7 -prune -exec rm -rf {} \;

# find was taking too much disk effort.  Switched to rm.
# Note - if this machine is off across one of the cron times, it will
# never delete the directories from 8 days previous.  Check every now and again.
olddate=$(/bin/date -d'8 days ago' +%Y%m%d.%H)
/bin/rm -rf /var/lib/ganglia/rrds.bak_${olddate}????


mydate=`/bin/date +%Y%m%d.%H%M%S`
nice -n 5 /bin/cp -a --no-preserve=timestamps /mnt/ram0/rrds /var/lib/ganglia/rrds.bak_${mydate}
