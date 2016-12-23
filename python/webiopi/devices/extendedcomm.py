## Copyright Overkiz

import serial
import time
import glob
from webiopi.utils.logger import debug

try:
    import _webiopi.GPIO as GPIO
except:
    pass

def	getFunctionFromStr(functionStr):
	function = -1

	if functionStr =="INP" :
		function = GPIO.IN
	elif functionStr == "OPP" :
		function = GPIO.OUT
	elif functionStr == "OOD" :
		function = GPIO.OUT
	else :
		raise Exception("Unknown function")
	return function

def	getStrFromFunction(function):
	functionStr = ""
	if function == GPIO.IN :
		functionStr = "INP"
	elif function == GPIO.OUT :
		functionStr = "OOD"
	else :
		raise Exception("POSTing function unknown")
	return functionStr

class ExtendedComm():
	def __init__(self, port):
		self.ser = serial.Serial()
		self.ser.baudrate = 230400
		self.ser.port = port

	def _write(self, message):
		self.ser.write(("%s\r" % message).encode('ascii'))
		time.sleep(1)
		out=''
		while self.ser.inWaiting() > 0:
			out += self.ser.read(1).decode('ascii')
		return out

	def connect(self):
		debug("Connect %s for device id %s" %(self.ser.baudrate, self.ser.port))
		self.ser.open()
		out = self._write("CONFIG DUMP")

		devices = []
		for line in out.splitlines():
			if line and line[0] == 'P': #How we recognize a gpio name
				temp = line.split(" ")
				dev = {"name": temp[0], "function": getFunctionFromStr(temp[1]), "value": temp[4]}
				devices.append(dev)
		return devices

	def disconnect(self):
		debug("Disconnect from %s" %(self.ser.port))
		self.ser.close()

	def read(self, channel):
		out = ''
		debug("read gpio %s" % channel)
		out = self._write("GET %s" % channel)

		value = -1
		if out.startswith("*OK*"):
			value = int(out.split(":")[1])
		elif out.startswith("*KO*"):
			debug("READ GPIOX KO : %s" % out)
			#Raise an error
		return value

	def write(self, channel, value):
		debug ("write gpio %s, with value %d" % (channel, value))
		out = self._write("SET %s %d" % (channel,value))

		if out.startswith("*KO*"):
			debug("WRITE GPIOX KO : %s" % out)
			#TODO Raise error

	def setfunction(self, channel, function):
		out = self._write("INIT %s SET %s NO" % (channel,getStrFromFunction(function)))
		time.sleep(1)
		while self.ser.inWaiting() > 0:
			out += self.ser.read(1).decode('ascii')
		if out.startswith("*KO*"):
			debug("READ GPIOX KO : %s" % out)
			#Raise an error

	def findCard(stid):
		ser = serial.Serial()
		ser.baudrate = 230400
		for port in glob.glob("/dev/ttyACM*"):
			ser.port = port
			ser.open()
			ser.write(("GETNAME\r").encode('ascii'))
			time.sleep(1)
			out=''
			while ser.inWaiting() > 0:
				out += ser.read(1).decode('ascii')

			if out.startswith("*OK*"):
				value = out.split(":")[1].rstrip()
				if(value == stid):
					ser.close()
					return port
				else:
					ser.close()
					continue
			elif out.startswith("*KO*"):
				debug("READ GPIOX KO : %s" % out)
				ser.close()
				#Raise an error
		return ""
