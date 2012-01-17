/*
 * This is the MIT License
 * http://www.opensource.org/licenses/mit-license.php
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 *
 */
package info.ganglia;

import java.io.IOException;
import java.net.DatagramPacket;
import java.net.InetAddress;
import java.net.MulticastSocket;

/**
 * Connects and sends packets to Ganglia via a multicast socket connection. If the multicast group is passed in as a constructor argument it will use that address.
 * Otherwise it will use the multicast group specified by the system env variable "ganglia.host"
 * 
 * @author Chris Bowling
 */
public class GConnector {

	private final static int DEFAULT_PORT = 8649;
	private final InetAddress inetAddress;
	private final MulticastSocket socket;

	/**
	 * Constructor uses multicastAddress specified in the System environment variable "ganglia.host" for its connection to ganglia.
	 * @throws IOException
	 */
	public GConnector() throws IOException {
		// read system env setting for Ganglia server address
		final String gangliaHostAddress = System.getProperty("ganglia.host");
		this.inetAddress = InetAddress.getByName(gangliaHostAddress);

		// create multicast socket, join group, and send meta data packet
		socket = new MulticastSocket(DEFAULT_PORT);
	}

	/**
	 * Constructor uses multicastAddress argument for its connection to Ganglia.
	 * @param multicastAddress address to send metadata and value data packets to
	 * @throws IOException
	 */
	public GConnector(String multicastAddress) throws IOException {
		this.inetAddress = InetAddress.getByName(multicastAddress);
		// create multicast socket, join group, and send meta data packet
		socket = new MulticastSocket(DEFAULT_PORT);
	}

	/**
	 * Creates a DatagramPacket using the byte[] argument and sends the packet to Ganglia.
	 * @param buf data formatted for Ganglia to be sent
	 * @param length byte[] length
	 */
	public void sendPacket(byte[] buf, int length) {
		try {
			final DatagramPacket packet = new DatagramPacket(buf, length, inetAddress, DEFAULT_PORT);
			socket.send(packet);
		} catch (IOException ioe) {
			ioe.printStackTrace();
		}
	}
}