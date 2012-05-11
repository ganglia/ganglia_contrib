require 'uuid'
require 'nokogiri'
require 'json'
# Maybe use defer, as this might take awhile
#  http://eventmachine.rubyforge.org/EventMachine.html#M000486
#  http://www.igvita.com/2008/05/27/ruby-eventmachine-the-speed-demon/
#  Separate thread
class PostCallbacks < Nokogiri::XML::SAX::Document

  attr_reader :metrics
  attr_reader :host
  attr_reader :base_timestamp

  def initialize(socket)
    @socket=socket
    @metrics=Array.new
    @host=:unknown
  end

  def start_element(element,attributes)
    if element == "METRIC"
      @metrics << metric_to_message(attributes)
    end

    # <CLUSTER NAME="mycluster" LOCALTIME="1319165001" OWNER="myself" LATLONG="" URL="">
    if element == "CLUSTER"
      attributes.each do |attribute|
        if attribute[0] == "LOCALTIME"
          @base_timestamp=attribute[1]

        end
      end
    end

    # Extract the hostname
    # # <HOST NAME="localhost.localdomain" IP="127.0.0.1" TAGS="" REPORTED="1319164995" 
    # #  TN="6" TMAX="20" DMAX="86400" LOCATION="0,0,0" GMOND_STARTED="1318994256">
    if element == "HOST"
      attributes.each do |attribute|
        if attribute[0] == "NAME"
          @host=attribute[1]
        end
      end
    end
  end

  def metric_to_message(attributes)
    message=Hash.new
    attributes.each do |attribute|
      name=attribute[0]
      value=attribute[1]
      message[name.downcase]=value
    end
    message['hostname']=@host
    return message
  end

  def end_document
    # At the end of the document send all metrics
    @metrics.each do |metric|
      message=Hash.new
      message['id']=UUID.new.generate

      # Correct the timestamp based on the time last seen
      message['timestamp']=@base_timestamp.to_i-message['tn'].to_i
      message['payload']=metric
      message['payload'].delete('source')
      message['context']="METRIC"
      message['source']="GMOND"

      # May have to decide on TMAX and DMAX not to send the metric any more
      # http://monami.sourceforge.net/tutorial/ar01s06.html
      @socket.send_msg('gmond', message.to_json)
    end
  end

end

class RemoteGmondHandler < EM::Connection
  attr_accessor :zmq_push_socket
  attr_accessor :verbose

  def receive_data data
    begin
      parser = Nokogiri::XML::SAX::Parser.new(PostCallbacks.new(zmq_push_socket))
      parser.parse(data)
    rescue ::Exception => ex
      puts "Error parsing XML: #{ex}"
    end
  end

  def unbind
    #puts "closing connection"
  end
end
