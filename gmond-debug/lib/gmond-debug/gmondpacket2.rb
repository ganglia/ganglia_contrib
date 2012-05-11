class GmonPacket2

  def initialize(packet)
    @unpacked=packet
    @result=Hash.new
    packet_type=unpack_int
    @result['gmetadata_full']=packet_type
    case packet_type[0]
    when 128 then unpack_meta
    when 132 then unpack_heartbeat
    when 134,133 then unpack_data
    end
  end

  def unpack_meta
    puts "got meta package"
    # This parse is only working correctly with gmetadata_full=128
    @result['hostname']=unpack_string
    @result['metricname']=unpack_string
    @result['spoof']=unpack_int
    @result['metrictype']=unpack_string
    @result['metricname2']=unpack_string
    @result['metricunits']=unpack_string
    @result['slope']=unpack_int
    @result['tmax']=unpack_int
    @result['dmax']=unpack_int
    nrelements=unpack_int
    @result['nrelements']=nrelements
    unless nrelements.nil?
      for i in 1..nrelements[0]
        name=unpack_string
        @result[name]=unpack_string
      end
    end
  end

  def unpack_data
    puts "got data package"
    unpack_data_blob
  end

  def unpack_data_blob
    @result['hostname']=unpack_string
    @result['metricname']=unpack_string
    @result['spoof']=unpack_int
    format=unpack_string
    @result['format']=format

    # Quick hack here
    # Needs real XDR parsing here
    # http://ruby-xdr.rubyforge.org/git?p=ruby-xdr.git;a=blob;f=lib/xdr.rb;h=b41177f32ae72f30d31122e5d801e4828a614c79;hb=HEAD
    @result['value']=unpack_float if format.include?("f")
    @result['value']=unpack_int if format.include?("u")
    @result['value']=unpack_string if format.include?("s")
  end

  def unpack_heartbeat
    puts "got heartbeat"
    unpack_data_blob
  end


  def unpack_int
    unless @unpacked.nil?
      value=@unpacked[0..3].unpack('N')
      shift_unpacked(4)
      return value
    else
      return nil
    end
  end

  def unpack_float
    unless @unpacked.nil?
      value=@unpacked[0..3].unpack('g')
      shift_unpacked(4)
      return value
    else
      return nil
    end
  end

  def unpack_string
    unless @unpacked.nil?
      size=@unpacked[0..3].unpack('N').to_s.to_i
      shift_unpacked(4)
      value=@unpacked[0..size-1]
      #The packets are padded
      shift_unpacked(size+((4-size) % 4))
      return value
    else
      return nil
    end
  end

  def shift_unpacked(count)
    @unpacked=@unpacked[count..@unpacked.length]
  end

  def to_hash
    return @result
  end

end
