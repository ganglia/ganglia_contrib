#!/usr/bin/env sh

if [ $# -gt 0 ]; then
   GANGLIA_CLUSTER=${1}
else
   GANGLIA_CLUSTER="cluster1"
fi

sed "s/GANGLIA_CLUSTER/$GANGLIA_CLUSTER/g" /etc/ganglia/gmond-template.conf > /etc/ganglia/gmond.conf

/usr/sbin/gmond -f -d1