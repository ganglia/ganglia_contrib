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
package info.ganglia.metric.type;

import info.ganglia.metric.GMetric;
import info.ganglia.metric.Incrementable;
import info.ganglia.metric.Metricable;

import java.io.IOException;


/**
 * Float implementation of GMetric. Uses method synchronization for thread safety.  
 * Performance loss from using this synchronization method is acknowledged and using the methods described in java.util.concurrent.atomic could improve this if necessary.  
 * 
 * @author Chris Bowling
 */
public class GMetricFloat extends GMetric implements Metricable, Incrementable {
	private float valueFloat = 0;

	/**
	 * 
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
	public GMetricFloat(String host, String name, String type, String units, int slope, boolean additive) {
		super(host, name, type, units, slope, additive);
	}

	/* (non-Javadoc)
	 * @see info.ganglia.metric.Incrementable#incrementValue()
	 */
	public synchronized void incrementValue() {
		valueFloat++;
	}

	/**
	 * Increments current GMetric value by value argument
	 * @param value increment GMetric value by value argument
	 */
	public synchronized void incrementValue(float value) {
		valueFloat += value;
	}

	/**
	 * Sets current GMetric value to value argument
	 * @param value set GMetric to new value
	 */
	public synchronized void setValue(float value) {
		valueFloat = value;
	}

	/* (non-Javadoc)
	 * @see info.ganglia.metric.Metricable#clearValue()
	 */
	public synchronized void clearValue() {
		valueFloat = 0;
	}

	/* (non-Javadoc)
	 * @see info.ganglia.metric.Metricable#getValueData()
	 */
	public byte[] getValueData() {
		byte[] valueBytes = null;
		valueBytes = writeValue(Float.toString(valueFloat));
		return valueBytes;
	}
}
