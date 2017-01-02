## Copyright Overkiz

from webiopi.utils.types import M_JSON
from webiopi.utils.logger import debug
from webiopi.devices.digital import GPIOPort
from webiopi.decorators.rest import request, response
from webiopi.devices.extendedcomm import ExtendedComm

try:
    import _webiopi.GPIO as GPIO
except:
    pass

#Gpio : {"name":"PE11", "function":"IN", "value":1}
#Card : {"name":"toto", "comm":ExtendendComm(), "gpios":List of gpio}
class ExtendedGPIO(GPIOPort):
	def __init__(self):
		#TODO Change the count to match exact count (not NEEDED currently)
		GPIOPort.__init__(self, 33)
		#TODO Get those values back from config file (not NEEDED currently)
		self.post_value = True
		self.post_function = True
		#card lists
		self.cards = []

	def __str__(self):
		return "GPIOX"

    #Add Card from setup
	def addCards(self, cardnames):
		for name in cardnames.split(" "):
			card = {}
			# Path to the USB serial device : /dev/ttyACM...
			card['name'] = name
			card['comm'] = ExtendedComm(name)
			self.cards.append(card)

	def findCard(self, cardname):
		for card in self.cards:
			if card['name'] == cardname:
				return card
		#TODO Create a new exception for this case
		raise GPIO.InvalidChannelException("Card %s does not exists" % cardname)

	def close(self):
		for card in self.cards:
			card['comm'].disconnect()

	#Find gpio on a card
	def getGpio(self, card, channel):
		for gpio in card['gpios']:
			if(gpio['name'] == channel):
				return gpio
		raise GPIO.InvalidChannelException("Gpio %s does not exists on card %s" % (channel, card['name']))

	def checkPostingFunctionAllowed(self):
		if not self.post_function:
			raise ValueError("POSTing function to GPIO not allowed")

	def checkPostingValueAllowed(self):
		if not self.post_value:
			raise ValueError("POSTing value to GPIO not allowed")

	def __digitalWrite__(self, card, channel, value):
		self.checkPostingValueAllowed()
		card['comm'].write(channel, value)

	def _getFunction_(self, gpio):
		func = gpio['function']
		if func == GPIO.IN:
			return "IN"
		elif func == GPIO.OUT:
			return "OUT"
		else:
			return "UNKNOWN"

	def _getFunctionString_(self, card, channel):
		gpio = self.getGpio(card, channel)
		return self._getFunction_(gpio)

	def __setFunction__(self, card, channel, value):
		self.checkPostingFunctionAllowed()
		card['comm'].setfunction(channel, value)

	def setFunction(self, card, channel, value):
		gpio = self.getGpio(card, channel)
		gpio['function'] = value
		self.__setFunction__(card, channel, value)
		return self._getFunction_(gpio)

	def _digitalRead_(self,card, channel):
		return card['comm'].read(channel)

	@request("GET", "%(card)s/count")
	@response("%d")
	#TODO Add correct count if needed
	def digitalCount(self,card):
		return 33

	@request("GET", "*")
	@response(contentType=M_JSON)
	def wildcard(self, compact=False):
		#TODO This is used to get the whole list of gpio status
		#(not NEEDED currently)
		return False

	@request("GET", "%(cardname)s/%(channel)s/function")
	def getFunctionString(self, cardname, channel):
		card = self.findCard(cardname)
		return self._getFunctionString_(card, channel)

	@request("POST", "%(cardname)s/%(channel)s/function/%(value)s")
	def setFunctionString(self, cardname, channel, value):
		self.checkPostingFunctionAllowed()
		card = self.findCard(cardname)
		value = value.lower()
		if value == "in":
			self.setFunction(card, channel, self.IN)
		elif value == "out":
			self.setFunction(card, channel, self.OUT)
		else:
			raise ValueError("Bad Function")
		return self._getFunctionString_(card, channel)

	@request("GET", "%(cardname)s/%(channel)s/value")
	@response("%d")
	def digitalRead(self, cardname, channel):
		card = self.findCard(cardname)
		return self._digitalRead_(card, channel)

	@request("POST", "%(cardname)s/%(channel)s/value/%(value)d")
	@response("%d")
	def digitalWrite(self, cardname, channel, value):
		self.checkPostingFunctionAllowed()
		self.checkDigitalValue(value)
		card = self.findCard(cardname)
		self.__digitalWrite__(card, channel, value)
		return self._digitalRead_(card, channel)

	@request("POST", "%(cardname)s/%(channel)s/trigger/%(value)d/duration/%(timems)d")
	@response("%d")
	def digitalTrigger(self, cardname, channel, value, timems):
		card = self.findCard(cardname)
		card['comm'].trigger(channel, value, timems)
		return 1

