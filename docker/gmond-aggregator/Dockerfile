FROM debian:jessie

MAINTAINER Vladimir Vuksan <vlemp@vuksan.com>

#RUN apt-get update
#RUN apt-get upgrade -y

# Install gmond aka ganglia-monitor
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y ganglia-monitor

EXPOSE 8649

# Copy gmond.conf from the current Dockerfile directory to /etc/ganglia/gmond-template.conf
ADD gmond.conf /etc/ganglia/gmond-template.conf
ADD entrypoint.sh /entrypoint.sh

# Command to execute when container starts up
ENTRYPOINT ["/entrypoint.sh"]
CMD ["test-cluster"]
