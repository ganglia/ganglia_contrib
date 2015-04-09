Included in the two directories are Dockerfiles to install Ganglia using Docker.

# Requirements

You need to have a current version of Docker installed.


# Build images

First we'll build the gmetad-ganglia web container. This will run Gmetad and the Web interface

<pre>
sudo docker build -t gmetad-gangliaweb gmetad-gangliaweb/.
</pre>

Secondly we'll build the gmond-aggregator container which will kick off a single gmond aggregator

<pre>
sudo docker build -t gmond-aggregator gmond-aggregator/.
</pre>

# Create configuration files and directories

We are going to create gmetad configuration file and RRD storage outside of the container
and just mount it inside the gmetad container. This is so we can persist it easily

For example we'll need to do something like this

<pre>
mkdir -p /var/lib/ganglia/rrds
chown -R 999:999 /var/lib/ganglia
cat <<ENDOF > /etc/ganglia/gmetad.conf
data_source "cluster1" gmond1:8649
setuid_username "ganglia"
case_sensitive_hostnames 0
ENDOF
</pre>

# Start up containers

First we start up the gmond-aggregator container. 

<pre>
sudo docker run -d -p 8649:8649/udp --name gmond1 gmond-aggregator
</pre>

Secondly we start up gmetad-gangliaweb container

<pre>
sudo docker run -d --name gmetad1 \
	-v /etc/ganglia/gmetad.conf:/etc/ganglia/gmetad.conf \
	-v /var/lib/ganglia:/var/lib/ganglia \
	--link gmond1:gmond1 \
	-p 0.0.0.0:80:80 ganglia-aggregator
</pre>

# Explanation

What will happen here is following

  - Gmond aggregator will be started on port 8649. It will expose UDP port 8649 on the host hosting the containers. That host is going to be
    called gmond1
  - When we launch gmetad-gangliaweb container it will mount /var/lib/ganglia and /etc/ganglia/gmetad.conf from the
  docker host inside the container
  - In addition gmond1 container will be linked with the gmetad1 container so gmetad1 can access it
  - Using --link will assure that /etc/hosts file in gmetad1 container is updated with the internal IP for gmond1

