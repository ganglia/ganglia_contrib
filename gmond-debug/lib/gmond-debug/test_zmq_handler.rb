class TestZmqHandler
  attr_reader :received
  def on_readable(socket, messages)
    messages[1..-1].each do |m|
      puts m.copy_out_string
    end
  end
end
