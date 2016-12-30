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
	cardname=""
	
	def __init__(self, cardname):
		self.cardname = cardname
		self.ser = serial.Serial()
		self.ser.baudrate = 230400
		self.ser.port = ""

	def _findPort(self):
		path = self.findCard()
		if path == "":
			debug("Card %s is not connected to this device" % self.cardname)
		else:
			self.ser.port = path

	def _write(self, message):
		self.ser.write(("%s\r" % message).encode('ascii'))
		time.sleep(1)
		out=''
		while self.ser.inWaiting() > 0:
			out += self.ser.read(1).decode('ascii')
		return out

	def _connect(self):
		self._findPort()
		try:
			self.ser.open()
		except:
			debug("Error connecting to card %s on port %s" %(self.cardname, self.ser.port)) 
		
	def _disconnect(self):
		self.ser.close()
		self.ser.port = ""

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
		self.ser.close()
		return devices

	def disconnect(self):
		debug("Disconnect from %s" %self.cardname)

	def read(self, channel):
		if self._connect() == -1 :
			return -1
		
		out = ''
		debug("read gpio %s" % channel)
		out = self._write("GET %s" % channel)

		value = -1
		if out.startswith("*OK*"):
			value = int(out.split(":")[1])
		elif out.startswith("*KO*"):
			debug("READ GPIOX KO : %s" % out)
			#Raise an error
		
		self.ser.close()
		self._disconnect()
		return value

	def write(self, channel, value):
		if self._connect() == -1 :
			return -1
			
		debug ("write gpio %s, with value %d" % (channel, value))
		out = self._write("SET %s %d" % (channel,value))

		if out.startswith("*KO*"):
			debug("WRITE GPIOX KO : %s" % out)
			#TODO Raise error
		self._disconnect()

	def setfunction(self, channel, function):
		if self._connect() == -1 :
			return -1
			
		out = self._write("INIT %s SET %s NO" % (channel,getStrFromFunction(function)))
		time.sleep(1)
		while self.ser.inWaiting() > 0:
			out += self.ser.read(1).decode('ascii')
		if out.startswith("*KO*"):
			debug("READ GPIOX KO : %s" % out)
			#Raise an error
		self._disconnect()

	def findCard(self):
	
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
				if(value == self.cardname):
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
