#!/usr/bin/ruby -d

#################################################################################
# Parse Ganglia XML stream and send metrics to Graphite
# License: Same as Ganglia
# Author: Vladimir Vuksan
# Modified from script written by: Vladimir Vuksan
# at https://github.com/ganglia/ganglia_contrib/blob/master/graphite_integration/ganglia_graphite.rb
#
# WARNING: Don't be surprised Carbon does not understand COUNTER type. You have to apply a derivative function in the UI.
#
#################################################################################
require "rubygems"
require "nokogiri"
require 'socket'

# Adjust to the appropriate values
ganglia_hostname = 'localhost'
ganglia_port = 8651
graphite_host = 'localhost'
graphite_port = 2003
debug = false

begin
  # Open up a socket to gmond
  file = TCPSocket.open(ganglia_hostname, ganglia_port)
  # Open up a socke to graphite
  graphite = TCPSocket.open(graphite_host, graphite_port)
  # We need current time stamp in UNIX time
  now = Time.now.to_i
  # Parse the XML we got from gmond
  doc = Nokogiri::XML file
  #doc.write( $stdout, 0 )

  #only one grid for now?

  # Set metric prefix to the host name. Graphite uses dots to separate subtrees
  # therefore we have to change dots in hostnames to _
  # Do substitution of whitespace after XML parsing to avoid problems with
  # pre-exiting whitespace in GRID / CLUSTER names in XML.

  grid = doc.at('GANGLIA_XML/GRID')
  grid_name = grid['NAME'].gsub(/\W/, "_")
  puts "GRID: #{grid['NAME']}" if debug

  grid.css('CLUSTER').each do |cluster|
    cluster_name=cluster["NAME"].gsub(/\W/, "_")
    puts "CLUSTER: #{cluster_name}" if debug

    cluster.css("HOST").each do |host|

      metric_prefix=host["NAME"].gsub(".", "_")
      puts "PREFIX: #{metric_prefix}" if debug

      host.css("METRIC").each do |metric|
        metric_name = metric["NAME"]
        puts "METRIC: #{metric_name}" if debug

        if metric["TYPE"] != "string"

          group = metric.at("EXTRA_DATA/EXTRA_ELEMENT[@NAME=GROUP]")
          if group
            group_name = group['VAL']
          else
            #Trick for gmetric < 3.2 (do not have --group option)
            #Name your metric group_metric_name
            split = metric_name.split('_')
            if split.count == 1
              group_name = 'nogroup'
            else
              group_name = split[0]
              metric_name = split[1..-1].join('_')
            end
          end

          puts "GROUP: #{group_name}" if debug

          cmd = "#{grid_name}.#{cluster_name}.#{metric_prefix}.#{group_name}.#{metric_name} #{metric["VAL"]} #{now}\n"
          debug ? puts(cmd) : graphite.puts(cmd)
        end
      end
    end

  end

  graphite.close()
  file.close()
rescue
# ignored
end
