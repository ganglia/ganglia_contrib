#!/usr/bin/ruby -d

#################################################################################
# Parse Ganglia XML stream and send metrics to Graphite
# License: Same as Ganglia
# Author: Vladimir Vuksan
# Modified from script written by: Kostas Georgiou
#################################################################################
require "rexml/document"
require 'socket'

# Adjust to the appropriate values
ganglia_hostname = 'localhost'
ganglia_port = 8649
graphite_host = "localhost"
graphite_port = "2003"
Debug = false

begin
  # Open up a socket to gmond
  file = TCPSocket.open(ganglia_hostname, ganglia_port)
  # Open up a socke to graphite
  graphite = TCPSocket.open(graphite_host, graphite_port)
  # We need current time stamp in UNIX time 
  now = Time.now.to_i
  # Parse the XML we got from gmond
  doc = REXML::Document.new file

  # Set the cluster name as path root
  cluster_prefix=nil
  doc.elements.each("GANGLIA_XML/CLUSTER") { |element| 
   # Convert all non Word characters to _
   cluster_prefix=element.attributes["NAME"].gsub(/\W/, "_")
  }

  doc.elements.each("GANGLIA_XML/CLUSTER/HOST") { |element|
    # Set metric prefix to the host name. Graphite uses dots to separate subtrees
    # therefore we have to change dots in hostnames to _
    metric_prefix=element.attributes["NAME"].gsub(".", "_")
    element.elements.each("METRIC") { |metric|
      if metric.attributes["TYPE"] != "string"                     
        graphite.puts "#{cluster_prefix}.#{metric_prefix}.#{metric.attributes["NAME"]} #{metric.attributes["VAL"]} #{now}\n"
        puts "#{cluster_prefix}.#{metric_prefix}.#{metric.attributes["NAME"]} #{metric.attributes["VAL"]} #{now}\n" if Debug
      end
    }
  }
  graphite.close()
  file.close()
rescue
end
