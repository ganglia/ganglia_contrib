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

import info.ganglia.metric.GMetric;
import info.ganglia.metric.Metricable;
import info.ganglia.metric.type.GMetricDouble;
import info.ganglia.metric.type.GMetricFloat;
import info.ganglia.metric.type.GMetricInteger;
import info.ganglia.metric.type.GMetricString;

import java.io.IOException;
import java.net.InetAddress;
import java.util.ArrayList;
import java.util.List;
import java.util.Random;
import java.util.TimerTask;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

/**
 * A Java interface that creates and updates metrics via Ganglia. At instantiation of a GMetric this sends a metadata packet with information for
 * creating the Ganglia graph. At a specified period of time (in seconds) will iterate through all monitored Metrics and send a packet containing the updated value to the connector.
 * If no period is specified in the constructor the default period of 60 seconds is used. Not compatible with previous versions of Ganglia.
 * 
 * @author Chris Bowling
 */
public class GMonitor {

	private static final long delay = 10; // default delay for 10 sec
	private static final long initPeriod = 5; // default period 5 requests -- Note graph may drop off if init not sent for extended period of time
	private long period = 60; // default period between requests 60 sec

	private List<Metricable> gmetrics;
	private GConnector connection;
	private int updateCount = 0;

	/**
	 * Constructor uses the default monitoring period to set update period and will use the multicastAddress specified in the System environment variable "ganglia.host" for its connection to Ganglia.	 
	 * @throws IOException
	 */
	public GMonitor() throws IOException {
		gmetrics = new ArrayList<Metricable>();
		connection = new GConnector();
		setMonitor();
	}

	/**
	 * Constructor uses monitoring period argument to set update period and will use the multicastAddress specified in the System environment variable "ganglia.host" for its connection to Ganglia.	 
	 * @param period time between value updates being sent to Ganglia. In seconds.
	 * @throws IOException
	 */
	public GMonitor(long period) throws IOException {
		this.period = period;
		gmetrics = new ArrayList<Metricable>();
		connection = new GConnector();
		setMonitor();
	}

	/**
	 * Constructor uses default monitoring period to set update period and will use the multicastAddress argument for its connection to ganglia.
	 * @param multicastAddress address to send metadata and value data packets to
	 * @throws IOException
	 */
	public GMonitor(String multicastAddress) throws IOException {
		gmetrics = new ArrayList<Metricable>();
		connection = new GConnector(multicastAddress);
		setMonitor();
	}

	/**
	 * Constructor uses the multicastAddress argument for its connection to ganglia and will use the monitoring period argument for time between value updates being sent
	 * @param multicastAddress address to send metadata and value data packets to
	 * @param period time between value updates being sent to ganglia. In seconds.
	 * @throws IOException
	 */
	public GMonitor(String multicastAddress, long period) throws IOException {
		this.period = period;
		gmetrics = new ArrayList<Metricable>();
		connection = new GConnector(multicastAddress);
		setMonitor();
	}

	/**
	 * Given the Metric type this creates a type specific GMetric implementation and adds it to the list of metrics to be monitored.  Upon creation sendGMetricInit and sendGMetricUpdate are called.
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
	 * @return 
	 */
	public Metricable createGMetric(String host, String name, String type, String units, int slope, boolean clearValues) {
		Metricable gmetric = null;
		if (GMetric.VALUE_TYPE_INT.equals(type)) {
			gmetric = new GMetricInteger(host, name, type, units, slope, clearValues);
		} else if (GMetric.VALUE_TYPE_STRING.equals(type)) {
			gmetric = new GMetricString(host, name, type, units, slope, clearValues);
		} else if (GMetric.VALUE_TYPE_FLOAT.equals(type)) {
			gmetric = new GMetricFloat(host, name, type, units, slope, clearValues);
		} else if (GMetric.VALUE_TYPE_DOUBLE.equals(type)) {
			gmetric = new GMetricDouble(host, name, type, units, slope, clearValues);
		} else {
			throw new IllegalArgumentException("unknown metric type");
		}
		gmetrics.add(gmetric);
		sendGMetricInit(gmetric);
		sendGMetricUpdate(gmetric);
		return gmetric;
	}

	/**
	 * Initializes the Metric by sending a metadata packet to the connector.
	 * @param gmetric GMetric to be initialized
	 */
	private void sendGMetricInit(Metricable gmetric) {
		if (null != gmetric){
			byte[] buf = gmetric.getMetaData();
			connection.sendPacket(buf, buf.length);
		}
	}

	/**
	 * Updates the Metric by sending a value packet to the connector.
	 * @param gmetric GMetric to be updated
	 */
	private void sendGMetricUpdate(Metricable gmetric) {
		if (null != gmetric){
			byte[] buf = gmetric.getValueData();
			connection.sendPacket(buf, buf.length);
		}
	}

	/**
	 * Instantiates the ScheduledExecutorService which will iterate through all monitored Metrics at the specified period, 
	 * send the current value of the Metric, and then clear the value.
	 */
	private void setMonitor() {
		ScheduledExecutorService eScheduledService = Executors.newSingleThreadScheduledExecutor();
		eScheduledService.scheduleAtFixedRate(new TimerTask() {
			public void run() {
				updateCount++;
				for (Metricable gmetric : gmetrics) {
					if (updateCount > initPeriod) {
						sendGMetricInit(gmetric);
					}
					sendGMetricUpdate(gmetric);

					if (!gmetric.isAdditive()) {
						gmetric.clearValue();
					}
				}
				if (updateCount > initPeriod) {
					updateCount = 0;
				}
			}
		}, delay, period, TimeUnit.SECONDS);
	}

	/**
	 * Usage: java -jar GangliaMetrics.jar multicastAddress
	 * 
	 * @param args
	 * @throws Exception
	 */
	public static void main(String args[]) throws Exception {
		final String host = InetAddress.getLocalHost().getHostName();
		if (args.length != 1) {
			System.out.println("Usage: java -jar GangliaMetrics.jar <multicast address>");
			return;
		}
		final String multicastAddress = args[0];
		if (null == multicastAddress || multicastAddress.trim().equals("")) {
			System.out.println("Usage: java -jar GangliaMetrics.jar <multicast address>");
			return;
		}
		GMonitor gmon = new GMonitor(multicastAddress, 30l);
		GMetricInteger testMetric = (GMetricInteger) gmon.createGMetric(host, "Ganglia Int Test", GMetric.VALUE_TYPE_INT, "count", GMetric.SLOPE_UNSPECIFIED, false);
		GMetricDouble testMetric2 = (GMetricDouble) gmon.createGMetric(host, "Ganglia Double Test ", GMetric.VALUE_TYPE_DOUBLE, "count2", GMetric.SLOPE_UNSPECIFIED, false);

		Random generator = new Random();
		int count = 0;
		double countDouble = 0;
		while(true) {
			Thread.sleep(5000);
			count = generator.nextInt(100);
			countDouble = generator.nextDouble() * 100;
			System.out.println(count);
			System.out.println(countDouble);
			testMetric.incrementValue(count);
			testMetric2.incrementValue(countDouble);
		}
	}
}