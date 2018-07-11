import sys
import ctypes
from Phidget22.PhidgetSupport import PhidgetSupport
from Phidget22.LogLevel import LogLevel
from Phidget22.PhidgetException import PhidgetException

class Log:

	def __init__(self):
		self.handle = ctypes.c_void_p()


	def __del__(self):
			pass

	@staticmethod
	def disable():
		try:
			__func = PhidgetSupport.getDll().PhidgetLog_disable
			__func.restype = ctypes.c_int32
			result = __func()
		except RuntimeError:
			raise

		if result > 0:
			raise PhidgetException(result)


	@staticmethod
	def enable(level, destination):
		_level = ctypes.c_int(level)
		_destination = ctypes.create_string_buffer(destination.encode('utf-8'))

		try:
			__func = PhidgetSupport.getDll().PhidgetLog_enable
			__func.restype = ctypes.c_int32
			result = __func(_level, ctypes.byref(_destination))
		except RuntimeError:
			raise

		if result > 0:
			raise PhidgetException(result)


	@staticmethod
	def getLevel():
		_level = ctypes.c_int()

		try:
			__func = PhidgetSupport.getDll().PhidgetLog_getLevel
			__func.restype = ctypes.c_int32
			result = __func(ctypes.byref(_level))
		except RuntimeError:
			raise

		if result > 0:
			raise PhidgetException(result)

		return _level.value

	@staticmethod
	def setLevel(level):
		_level = ctypes.c_int(level)

		try:
			__func = PhidgetSupport.getDll().PhidgetLog_setLevel
			__func.restype = ctypes.c_int32
			result = __func(_level)
		except RuntimeError:
			raise

		if result > 0:
			raise PhidgetException(result)


	@staticmethod
	def log(level, message):
		_level = ctypes.c_int(level)
		_message = ctypes.create_string_buffer(message.encode('utf-8'))

		try:
			__func = PhidgetSupport.getDll().PhidgetLog_log
			__func.restype = ctypes.c_int32
			result = __func(_level, ctypes.byref(_message))
		except RuntimeError:
			raise

		if result > 0:
			raise PhidgetException(result)


	@staticmethod
	def rotate():
		try:
			__func = PhidgetSupport.getDll().PhidgetLog_rotate
			__func.restype = ctypes.c_int32
			result = __func()
		except RuntimeError:
			raise

		if result > 0:
			raise PhidgetException(result)


	@staticmethod
	def isRotating():
		_isrotating = ctypes.c_int()

		try:
			__func = PhidgetSupport.getDll().PhidgetLog_isRotating
			__func.restype = ctypes.c_int32
			result = __func(ctypes.byref(_isrotating))
		except RuntimeError:
			raise

		if result > 0:
			raise PhidgetException(result)

		return _isrotating.value

	@staticmethod
	def getRotating():
		_size = ctypes.c_uint64()
		_keepCount = ctypes.c_int()

		try:
			__func = PhidgetSupport.getDll().PhidgetLog_getRotating
			__func.restype = ctypes.c_int32
			result = __func(ctypes.byref(_size), ctypes.byref(_keepCount))
		except RuntimeError:
			raise

		if result > 0:
			raise PhidgetException(result)

		return _size.value, _keepCount.value

	@staticmethod
	def setRotating(size, keepCount):
		_size = ctypes.c_uint64(size)
		_keepCount = ctypes.c_int(keepCount)

		try:
			__func = PhidgetSupport.getDll().PhidgetLog_setRotating
			__func.restype = ctypes.c_int32
			result = __func(_size, _keepCount)
		except RuntimeError:
			raise

		if result > 0:
			raise PhidgetException(result)


	@staticmethod
	def enableRotating():
		try:
			__func = PhidgetSupport.getDll().PhidgetLog_enableRotating
			__func.restype = ctypes.c_int32
			result = __func()
		except RuntimeError:
			raise

		if result > 0:
			raise PhidgetException(result)


	@staticmethod
	def disableRotating():
		try:
			__func = PhidgetSupport.getDll().PhidgetLog_disableRotating
			__func.restype = ctypes.c_int32
			result = __func()
		except RuntimeError:
			raise

		if result > 0:
			raise PhidgetException(result)


	@staticmethod
	def getSourceLevel(source):
		_source = ctypes.create_string_buffer(source.encode('utf-8'))
		_level = ctypes.c_int()

		try:
			__func = PhidgetSupport.getDll().PhidgetLog_getSourceLevel
			__func.restype = ctypes.c_int32
			result = __func(ctypes.byref(_source), ctypes.byref(_level))
		except RuntimeError:
			raise

		if result > 0:
			raise PhidgetException(result)

		return _level.value

	@staticmethod
	def setSourceLevel(source, level):
		_source = ctypes.create_string_buffer(source.encode('utf-8'))
		_level = ctypes.c_int(level)

		try:
			__func = PhidgetSupport.getDll().PhidgetLog_setSourceLevel
			__func.restype = ctypes.c_int32
			result = __func(ctypes.byref(_source), _level)
		except RuntimeError:
			raise

		if result > 0:
			raise PhidgetException(result)

