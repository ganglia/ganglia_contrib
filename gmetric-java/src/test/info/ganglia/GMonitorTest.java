package info.ganglia;

import static org.junit.Assert.assertTrue;
import static org.junit.Assert.fail;

import info.ganglia.GMonitor;
import info.ganglia.metric.GMetric;
import info.ganglia.metric.Metricable;
import info.ganglia.metric.type.GMetricInteger;

import java.io.IOException;
import java.net.InetAddress;

import org.junit.BeforeClass;
import org.junit.Test;


public class GMonitorTest {
	public final static String MULTICAST_ADDRESS = "239.0.0.0";
	private static String host;
	
	@BeforeClass
	public static void oneTimeSetUp() throws Exception {
		System.setProperty("ganglia.host", "239.0.0.0");
		host = InetAddress.getLocalHost().getHostName();
	}
	

	@Test
	@SuppressWarnings("unused")
	public void testConstructor() {
		try {
			GMonitor gmon = new GMonitor();
			GMetricInteger testMetric = (GMetricInteger) gmon.createGMetric(host, "Ganglia Test", GMetric.VALUE_TYPE_INT, "count", GMetric.SLOPE_UNSPECIFIED, true);
		} catch (IOException e) {
			e.printStackTrace();
			fail();
		}
	}

	@Test
	@SuppressWarnings("unused")
	public void testConstructor2() {
		try {
			GMonitor gmon = new GMonitor(30l);
			GMetricInteger testMetric = (GMetricInteger) gmon.createGMetric(host, "Ganglia Test", GMetric.VALUE_TYPE_INT, "count", GMetric.SLOPE_UNSPECIFIED, true);
		} catch (IOException e) {
			e.printStackTrace();
			fail();
		}
	}
	
	@Test
	@SuppressWarnings("unused")
	public void testConstructor3() {
		try {
			GMonitor gmon = new GMonitor(MULTICAST_ADDRESS);
			GMetricInteger testMetric = (GMetricInteger) gmon.createGMetric(host, "Ganglia Test", GMetric.VALUE_TYPE_INT, "count", GMetric.SLOPE_UNSPECIFIED, true);
		} catch (IOException e) {
			e.printStackTrace();
			fail();
		}
	}
	
	@Test
	@SuppressWarnings("unused")
	public void testConstructor4() {
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
	public void testConstructorNullArgsConst1() {
		try {
			GMetric gmetric = new GMetric(null, "Ganglia Test", GMetric.VALUE_TYPE_INT, "count", GMetric.SLOPE_UNSPECIFIED, true);
		} catch (IllegalArgumentException e) {
			assertTrue(true);
		}
		
		try {
			GMetric gmetric = new GMetric(host, null, GMetric.VALUE_TYPE_INT, "count", GMetric.SLOPE_UNSPECIFIED, true);
		} catch (IllegalArgumentException e) {
			assertTrue(true);
		}
		
		try {
			GMetric gmetric = new GMetric(host, "Ganglia Test", null, "count", GMetric.SLOPE_UNSPECIFIED, true);
		} catch (IllegalArgumentException e) {
			assertTrue(true);
		}
		
		try {
			GMetric gmetric = new GMetric(host, "Ganglia Test", GMetric.VALUE_TYPE_INT, null, GMetric.SLOPE_UNSPECIFIED, true);
		} catch (IllegalArgumentException e) {
			assertTrue(true);
		}
	}
	
	@Test
	@SuppressWarnings("unused")
	public void testConstructorNullArgsConst2() {
		try {
			GMetric gmetric = new GMetric(host, "Ganglia Test", GMetric.VALUE_TYPE_INT, "count", GMetric.SLOPE_UNSPECIFIED, true);
		} catch (IllegalArgumentException e) {
			assertTrue(true);
		}catch (Exception e) {
			fail();
		}
		try {
			GMetric gmetric = new GMetric(null, "Ganglia Test", GMetric.VALUE_TYPE_INT, "count", GMetric.SLOPE_UNSPECIFIED, true);
		} catch (IllegalArgumentException e) {
			assertTrue(true);
		}catch (Exception e) {
			fail();
		}

		try {
			GMetric gmetric = new GMetric(host, null, GMetric.VALUE_TYPE_INT, "count", GMetric.SLOPE_UNSPECIFIED, true);
		} catch (IllegalArgumentException e) {
			assertTrue(true);
		}catch (Exception e) {
			fail();
		}
		
		try {
			GMetric gmetric = new GMetric(host, "Ganglia Test", null, "count", GMetric.SLOPE_UNSPECIFIED, true);
		} catch (IllegalArgumentException e) {
			assertTrue(true);
		}catch (Exception e) {
			fail();
		}
		
		try {
			GMetric gmetric = new GMetric(host, "Ganglia Test", GMetric.VALUE_TYPE_INT, null, GMetric.SLOPE_UNSPECIFIED, true);
		} catch (IllegalArgumentException e) {
			assertTrue(true);
		}catch (Exception e) {
			fail();
		}
	}
	
	@SuppressWarnings("unchecked")
	@Test
	public void testSendGMetricInit() {
		try {
			GMonitor gmon = new GMonitor(MULTICAST_ADDRESS, 30l);
			Class[] inputType = new Class[1];
			Object[] input = new Object[1];
			inputType[0] = Metricable.class;
			input[0] = null;
			UnitTestHelper.invokeMethod(gmon, "sendGMetricInit", inputType, input);
		} catch (Exception e) {
			e.printStackTrace();
			fail();
		}
	}
	
	@SuppressWarnings("unchecked")
	@Test
	public void testSendGMetricUpdate() {
		try {
			GMonitor gmon = new GMonitor(MULTICAST_ADDRESS, 30l);
			Class[] inputType = new Class[1];
			Object[] input = new Object[1];
			inputType[0] = Metricable.class;
			input[0] = null;
			UnitTestHelper.invokeMethod(gmon, "sendGMetricUpdate", inputType, input);
		} catch (Exception e) {
			e.printStackTrace();
			fail();
		}
	}
	@Test
	public void testMain() {
		try {
			String args [] = new String[1];
			args[0] = MULTICAST_ADDRESS;
			GMonitor.main(args);
		} catch (Exception e) {
			e.printStackTrace();
			fail();
		}
	}
	
	@Test
	public void testMain2() {
		try {
			String args [] = new String[1];
			args[0] = null;
			GMonitor.main(args);
		} catch (Exception e) {
			e.printStackTrace();
			fail();
		}
	}
	
	@Test
	public void testMain3() {
		try {
			String args [] = new String[0];
			GMonitor.main(args);
		} catch (Exception e) {
			e.printStackTrace();
			fail();
		}
	}
	
	@Test
	public void testMain4() {
		try {
			String args [] = new String[1];
			args[0] = "";
			GMonitor.main(args);
		} catch (Exception e) {
			e.printStackTrace();
			fail();
		}
	}
}
