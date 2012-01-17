package info.ganglia;

import java.lang.reflect.Method;


public class UnitTestHelper {

	@SuppressWarnings("unchecked")
	public static Object invokeMethod(Object targetObject, String methodName, Class[] argClasses, Object[] argObjects) {
		Object result = null;
		try {
			Method method = targetObject.getClass().getDeclaredMethod(methodName, argClasses);
			// this makes private methods accessible
			method.setAccessible(true);
			result = method.invoke(targetObject, argObjects);
			
		} catch (Exception e) {
			e.printStackTrace();
		}
		return result;
	}

	@SuppressWarnings("unchecked")
	public static Object invokeMethod(Class targetClass, Object targetObject, String methodName, Class[] argClasses, Object[] argObjects) {
		Object result = null;
		try {
			Method method = targetClass.getDeclaredMethod(methodName, argClasses);
			// this makes private methods accessible
			method.setAccessible(true);
			result = method.invoke(targetObject, argObjects);
			
		} catch (Exception e) {
			e.printStackTrace();
		}
		return result;
	}
}
