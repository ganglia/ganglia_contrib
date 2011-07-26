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
ganglia_port = 8651
graphite_host = 'localhost'
graphite_port = 2003
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
  #doc.write( $stdout, 0 )

  grid=nil
  doc.elements.each("GANGLIA_XML/GRID") { |element| 
   grid=element.attributes["NAME"]
  }
  puts "GRID: #{grid}\n" if Debug

  cluster=nil
  doc.elements.each("GANGLIA_XML/GRID/CLUSTER") { |element| 
   cluster=element.attributes["NAME"] 
    puts "CLUSTER: #{cluster}\n" if Debug

    doc.elements.each("GANGLIA_XML/GRID[@NAME='#{grid}']/CLUSTER[@NAME='#{cluster}']/HOST") { |host|
      metric_prefix=host.attributes["NAME"].gsub(".", "_")
      host.elements.each("METRIC") { |metric|
        # Set metric prefix to the host name. Graphite uses dots to separate subtrees
        # therefore we have to change dots in hostnames to _
        # Do substitution of whitespace after XML parsing to avoid problems with 
        # pre-exiting whitespace in GRID / CLUSTER names in XML. 
        grid.gsub!(/\W/, "_")
        cluster.gsub!(/\W/, "_")
        if metric.attributes["TYPE"] != "string"                     
          graphite.puts "#{grid}.#{cluster}.#{metric_prefix}.#{metric.attributes["NAME"]} #{metric.attributes["VAL"]} #{now}\n" if !Debug
          puts "#{grid}.#{cluster}.#{metric_prefix}.#{metric.attributes["NAME"]} #{metric.attributes["VAL"]} #{now}\n" if Debug
        end
      }
    }
  }

  graphite.close()
  file.close()
rescue
end
