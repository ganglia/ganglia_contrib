require 'uuid'
require 'gmond-debug/gmondpacket'
require 'json'

Thread.abort_on_exception = true

# Passing params to an EM Connection
#  http://stackoverflow.com/questions/3985092/one-question-with-eventmachine

class LocalGmondHandler < EM::Connection
  attr_accessor :zmq_push_socket
  attr_accessor :verbose

  def receive_data packet

    @metadata=Hash.new if @metadata.nil?

    gmonpacket=GmonPacket.new(packet)
    if gmonpacket.meta?
      # Extract the metadata from the packet
      meta=gmonpacket.parse_metadata
      # Add it to the global metadata of this connection
      @metadata[meta['name']]=meta
    elsif gmonpacket.data?
      data=gmonpacket.parse_data(@metadata)

      # Check if it was a valid data request
      unless data.nil?
        # We currently assume this goes fast
        # send Topic, Body
        # Using the correct helper methods - https://github.com/andrewvc/em-zeromq/blob/master/lib/em-zeromq/connection.rb

        message=Hash.new
        message['id'] = UUID.new.generate
        message['timestamp'] = Time.now.to_i
        message['context'] = "METRIC"
        message['source'] = "GMOND"
        message['payload'] = data
        %w{dmax tmax slope type units}.each do |info|
          message['payload'][info] = @metadata[data['name']][info]
        end
        # message['payload']['meta'] = @metadata[data['name']]

        puts message.to_json
        # zmq_push_socket.send_msg('gmond', message.to_json)
      end
    else
      # Skipping unknown packet types
    end


    # If not, we might need to defer the block
    # # http://www.igvita.com/2008/05/27/ruby-eventmachine-the-speed-demon/
    # # Callback block to execute once the parsing is finished
    # operation = proc do
    # end
    #
    # callback = proc do |res|
    # end
    # # Let the thread pool (20 Ruby Threads handle request)
    # EM.defer(operation,callback)

  end

end
