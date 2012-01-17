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
package info.ganglia.metric;

import java.io.ByteArrayOutputStream;
import java.io.DataOutputStream;
import java.io.IOException;

/**
 * Base class for GMetrics. Metrics are broken out and instantiated based on type for performance and scalability considerations. 
 * This class provides GMetric functionality unrelated to the specific GMetric type.
 * 
 * @author Chris Bowling
 */
public class GMetric {

	public final static int SLOPE_ZERO = 0;
	public final static int SLOPE_POSITIVE = 1;
	public final static int SLOPE_NEGATIVE = 2;
	public final static int SLOPE_BOTH = 3;
	public final static int SLOPE_UNSPECIFIED = 4;

	public final static String VALUE_TYPE_STRING = "string";
	public final static String VALUE_TYPE_INT = "int32";
	public final static String VALUE_TYPE_FLOAT = "float";
	public final static String VALUE_TYPE_DOUBLE = "double";

	private final String host;
	private final String name;
	private final String type;
	private final String units;
	private final int slope;
	private final byte[] metadata;
	
	private boolean additive = false;

	/**
	 * Constructor creates GMetric with specified arguments
	 * @param host
	 *            The hostname of the client server
	 * @param name
	 *            The name of the metric (e.g. "CPU Usage"). Shows on graph
	 * @param type
	 *            The type of the value. See GMetric constants.
	 * @param units
	 *            The units used to measure the metric. Shows on graph
	 * @param slope
	 *            See GMetric constants.
	 * @param additive
	 *            If false the GMetric values are reset to 0 after update.  If true the GMetric values are additive.        
	 * @throws IOException
	 */
	public GMetric(String host, String name, String type, String units, int slope, boolean additive) {
		if (null == host) {
			throw new IllegalArgumentException("host was null");
		}
		if (null == name) {
			throw new IllegalArgumentException("name was null");
		}
		if (null == type) {
			throw new IllegalArgumentException("type was null");
		}
		if (null == units) {
			throw new IllegalArgumentException("units was null");
		}
		this.host = host;
		this.name = name.replaceAll(" ", "");
		this.type = type;
		this.units = units;
		this.slope = slope;
		this.metadata = writeMeta();
		this.additive = additive;
	}

	/**
	 * Writes XDR representation of value and other Ganglia specific parameters to byte[]
	 * @param value GMetric value to be written
	 * @return byte[]
	 */
	protected byte[] writeValue(String value) {
		// value cannot be null. Even if it was null it would have no impact.
		ByteArrayOutputStream baos = new ByteArrayOutputStream();
		DataOutputStream dos = new DataOutputStream(baos);
		try {
			/*
			ganglia message formats 
			gmetadata_full = 128,
			gmetric_ushort = 129,
			gmetric_short = 130,
			gmetric_int = 131,
			gmetric_uint = 132,
			gmetric_string = 133,
			gmetric_float = 134,
			gmetric_double = 135
			*/
			// current implementation always writes String.  Could add support for other types.
			dos.writeInt(128 + 5); 
			writeXDRString(dos, host);
			writeXDRString(dos, name);
			dos.writeInt(0);
			writeXDRString(dos, "%s");
			writeXDRString(dos, value);
		} catch (IOException ioe) {
			ioe.printStackTrace();
		}
		return baos.toByteArray();
	}

	/**
	 * Writes XDR representation of GMetric metadata and other Ganglia specific parameters to byte[]
	 * @return byte[]
	 */
	private byte[] writeMeta() {
		ByteArrayOutputStream baos = new ByteArrayOutputStream();
		DataOutputStream dos = new DataOutputStream(baos);
		try {
			/*
			ganglia message formats 
			gmetadata_full = 128,
			gmetric_ushort = 129,
			gmetric_short = 130,
			gmetric_int = 131,
			gmetric_uint = 132,
			gmetric_string = 133,
			gmetric_float = 134,
			gmetric_double = 135
			*/
			dos.writeInt(128); // gmetadata_full
			writeXDRString(dos, host);
			writeXDRString(dos, name);
			dos.writeInt(0);
			writeXDRString(dos, type);
			writeXDRString(dos, name);
			writeXDRString(dos, units);
			dos.writeInt(slope);
			dos.writeInt(0);
		} catch (IOException ioe) {
			ioe.printStackTrace();
		}
		return baos.toByteArray();
	}

	/**
	 * Writes XDR representation to DataOutputStream
	 * @param dos 
	 * @param string
	 * @throws IOException
	 */
	private void writeXDRString(DataOutputStream dos, String string) throws IOException {
		if (null != dos && null != string) {
			dos.writeInt(string.length());
			dos.writeBytes(string);
			int offset = string.length() % 4;
			if (offset != 0) {
				for (int i = offset; i < 4; ++i) {
					dos.writeByte(0);
				}
			}
		}
	}

	/**
	 * Fetches metadata for this GMetric
	 * @return
	 */
	public byte[] getMetaData() {
		byte[] metaData = this.metadata;
		return metaData;
	}

	/**
	 * Returns false if this GMetric resets values to 0 after it sends an update or true if it's additive
	 * @return the clearValues
	 */
	public boolean isAdditive() {
		return additive;
	}
}
