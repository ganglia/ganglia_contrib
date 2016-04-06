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

```
sudo mkdir -p /var/lib/ganglia/rrds /etc/ganglia
sudo chown -R 999:999 /var/lib/ganglia
sudo sh -c "cat > /etc/ganglia/gmetad.conf <<EOL
data_source \"web-cluster\" gmond1:8649
data_source \"db-cluster\" gmond2:8649
setuid_username \"ganglia\"
# RRDCached_address available in Ganglia 3.7.0+
#rrdcached_address 127.0.0.1:9998
case_sensitive_hostnames 0
EOL"
```

# Start up containers

First we start up the gmond-aggregator container(s). You will need to run a separate Docker instance for
each cluster you want to support. For example

<pre>
sudo docker run -d -p 8649:8649/udp --name gmond1 gmond-aggregator web-cluster
</pre>

will start gmond aggregator on port 8649 for web-cluster. Please note we named the container gmond1
so we can easily refer to it later. To invoke further ones you will need to change the 
bind port on the left e.g. to invoke second aggregator type

<pre>
sudo docker run -d -p 12001:8649/udp --name gmond2 gmond-aggregator db-cluster
</pre>

Secondly we start up gmetad-gangliaweb container

<pre>
sudo docker run -d --name gmetad1 \
	-v /etc/ganglia/gmetad.conf:/etc/ganglia/gmetad.conf \
	-v /var/lib/ganglia:/var/lib/ganglia \
	--link gmond1:gmond1 \
	--link gmond2:gmond2 \
	-p 0.0.0.0:80:80 gmetad-gangliaweb
</pre>

# Explanation

What will happen here is following

  - Gmond aggregator will be started on port 8649. It will expose UDP port 8649 on the host hosting the containers. That host is going to be called gmond1. Same story with 
  - When we launch gmetad-gangliaweb container it will mount /var/lib/ganglia and /etc/ganglia/gmetad.conf from the docker host inside the container
  - In addition gmond1 container will be linked with the gmetad1 container so gmetad1 can access it
  - Using --link will assure that /etc/hosts file in gmetad1 container is updated with the internal IP for gmond1
  - Ganglia Web will be available on http://localhost/ganglia
