#!/bin/bash

DIR="/config"
graphite_user="_graphite"

cp $DIR/local_settings.py /etc/graphite/local_settings.py

cp $DIR/initial_data.json /usr/share/graphite-web/initial_data.json

if [ ! -f /var/lib/graphite/graphite.db ]
then

   cd /usr/share/graphite-web
   graphite-manage syncdb --noinput

fi

chown -R $graphite_user /var/lib/graphite