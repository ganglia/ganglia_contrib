package info.ganglia;

import static org.junit.Assert.assertTrue;
import static org.junit.Assert.fail;

import info.ganglia.GMonitor;
import info.ganglia.metric.GMetric;
import info.ganglia.metric.type.GMetricDouble;
import info.ganglia.metric.type.GMetricFloat;
import info.ganglia.metric.type.GMetricInteger;
import info.ganglia.metric.type.GMetricString;

import java.io.ByteArrayOutputStream;
import java.io.DataOutputStream;
import java.io.IOException;
import java.net.InetAddress;

import org.junit.BeforeClass;
import org.junit.Test;



public class GMetricTest {
	public final static String MULTICAST_ADDRESS = "239.0.0.0";
	private static String host;
	
	@BeforeClass
	public static void oneTimeSetUp() throws Exception {
		System.setProperty("ganglia.host", "239.0.0.0");
		host = InetAddress.getLocalHost().getHostName();
	}
	
	@Test
	@SuppressWarnings("unused")
	public void testMetricTypeConstructor() {
		try {
			GMonitor gmon = new GMonitor(MULTICAST_ADDRESS, 30l);
			GMetricInteger testMetric = (GMetricInteger) gmon.createGMetric(host, "Ganglia Test", GMetric.VALUE_TYPE_INT, "count", GMetric.SLOPE_UNSPECIFIED, true);
		} catch (IOException e) {
			e.printStackTrace();
			fail();
		}
	}
	@Test
	@SuppressWarnings("unused")
	public void testMetricTypeConstructor2() {
		try {
			GMonitor gmon = new GMonitor(MULTICAST_ADDRESS, 30l);
			GMetricString testMetric = (GMetricString) gmon.createGMetric(host, "Ganglia Test", GMetric.VALUE_TYPE_STRING, "count", GMetric.SLOPE_UNSPECIFIED, true);
		} catch (IOException e) {
			e.printStackTrace();
			fail();
		}
	}
	@Test
	@SuppressWarnings("unused")
	public void testMetricTypeConstructor3() {
		try {
			GMonitor gmon = new GMonitor(MULTICAST_ADDRESS, 30l);
			GMetricFloat testMetric = (GMetricFloat) gmon.createGMetric(host, "Ganglia Test", GMetric.VALUE_TYPE_FLOAT, "count", GMetric.SLOPE_UNSPECIFIED, true);
		} catch (IOException e) {
			e.printStackTrace();
			fail();
		}
	}
	@Test
	@SuppressWarnings("unused")
	public void testMetricTypeConstructor4() {
		try {
			GMonitor gmon = new GMonitor(MULTICAST_ADDRESS, 30l);
			GMetricDouble testMetric = (GMetricDouble) gmon.createGMetric(host, "Ganglia Test", GMetric.VALUE_TYPE_DOUBLE, "count", GMetric.SLOPE_UNSPECIFIED, true);
		} catch (IOException e) {
			e.printStackTrace();
			fail();
		}
	}
	
	@Test
	@SuppressWarnings("unused")
	public void testMetricTypeConstructor5() {
		try {
			GMonitor gmon = new GMonitor(MULTICAST_ADDRESS, 30l);
			GMetricInteger testMetric = (GMetricInteger) gmon.createGMetric(host, "Ganglia Test", "INVALID_TYPE", "count", GMetric.SLOPE_UNSPECIFIED, true);
		} catch (IllegalArgumentException e) {
			assertTrue(true);
		} catch (Exception e) {
			fail();
		}
	}
	
	@Test
	public void testUpdateInt() {
		int value = 10;
		try {
			GMonitor gmon = new GMonitor(MULTICAST_ADDRESS, 30l);
			GMetricInteger testMetric = (GMetricInteger) gmon.createGMetric(host, "Ganglia Test", GMetric.VALUE_TYPE_INT, "count", GMetric.SLOPE_UNSPECIFIED, true);
			testMetric.incrementValue(value);
			testMetric.incrementValue();
			testMetric.setValue(value);
		} catch (IOException e) {
			e.printStackTrace();
			fail();
		}
	}
	
	@Test
	public void testUpdateDouble() {
		double value = 10.50;
		try {
			GMonitor gmon = new GMonitor(MULTICAST_ADDRESS, 30l);
			GMetricDouble testMetric = (GMetricDouble) gmon.createGMetric(host, "Ganglia Test", GMetric.VALUE_TYPE_DOUBLE, "count", GMetric.SLOPE_UNSPECIFIED, true);
			testMetric.incrementValue(value);
			testMetric.incrementValue();
			testMetric.setValue(value);
		} catch (IOException e) {
			e.printStackTrace();
			fail();
		}
	}
	
	@Test
	public void testUpdateFloat() {
		float value = 10.50f;
		try {
			GMonitor gmon = new GMonitor(MULTICAST_ADDRESS, 30l);
			GMetricFloat testMetric = (GMetricFloat) gmon.createGMetric(host, "Ganglia Test", GMetric.VALUE_TYPE_FLOAT, "count", GMetric.SLOPE_UNSPECIFIED, true);
			testMetric.incrementValue(value);
			testMetric.incrementValue();
			testMetric.setValue(value);
		} catch (IOException e) {
			e.printStackTrace();
			fail();
		}
	}
	
	@Test
	public void testUpdateString() {
		String value = "10";
		try {
			GMonitor gmon = new GMonitor(MULTICAST_ADDRESS, 30l);
			GMetricString testMetric = (GMetricString) gmon.createGMetric(host, "Ganglia Test", GMetric.VALUE_TYPE_STRING, "count", GMetric.SLOPE_UNSPECIFIED, true);
			testMetric.setValue(value);
			testMetric.setValue(null);
		} catch (IOException e) {
			e.printStackTrace();
			fail();
		}
	}
	
	@SuppressWarnings("unchecked")
	@Test
	public void testWriteXDRString() {
		try {
			GMetric gmetric = new GMetric(host, "Ganglia Test", GMetric.VALUE_TYPE_INT, "count", GMetric.SLOPE_UNSPECIFIED, true);
			Class[] inputType = new Class[2];
			Object[] input = new Object[2];
			inputType[0] = DataOutputStream.class;
			inputType[1] = String.class;
			input[0] = null;
			input[1] = null;
			UnitTestHelper.invokeMethod(gmetric, "writeXDRString", inputType, input);
			input[0] = new DataOutputStream(new ByteArrayOutputStream());
			UnitTestHelper.invokeMethod(gmetric, "writeXDRString", inputType, input);
		} catch (Exception e) {
			e.printStackTrace();
			fail();
		}
	}
}