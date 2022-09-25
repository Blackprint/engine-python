from Blackprint.RoutePort import RoutePort
from .Constructor.CustomEvent import CustomEvent
from .Constructor.Port import Port as PortClass
from .Constructor.References import References
from .Constructor.PortLink import PortLink
from .Interface import Interface
from .Internal import Internal

class Node(CustomEvent):
	_outputLink: PortClass = {}
	output: PortLink = {}

	_inputLink: PortClass = {}
	input: PortLink = {}

	iface: Interface = None
	_contructed = False
	disablePorts = False
	routes: RoutePort = None

	ref: References = None

	# Reserved for future
	# @param Engine instance 
	def __init__(this, instance):
		this.contructed = True

	def setInterface(this, namespace='BP/default'):
		if(this.iface != None):
			raise Exception('node.setInterface() can only be called once')

		if(this.contructed == False):
			raise Exception("Make sure you have call 'Node.__init__(instance);' when constructing nodes before '.setInterface'")

		if(Internal.interface.has_key(namespace) == False):
			raise Exception(f"Node interface for '[{namespace}]' was not found, maybe .registerInterface() haven't being called?")

		iface = Internal.interface[namespace](this)
		this.iface = iface

		return iface

	def createPort(this, which, name, type):
		if(which != 'input' and which != 'output'):
			raise Exception("Can only create port for 'input' and 'output'")

		if(which == "input"):
			return this._inputLink._add(name, type)
		else: return this._outputLink._add(name, type)

	def renamePort(this, which, name, to):
		iPort = this.iface[which]

		if(not iPort.has_key(name)):
			raise Exception("$which port with name '$name' was not found")

		if(iPort.has_key(to)):
			raise Exception("$which port with name '$to' already exist")

		temp = iPort[name]
		iPort[to] = temp
		del iPort[name]

		temp.name = to
		this[which][to] = this[which][name]
		del this[which][name]

	def deletePort(this, which, name):
		if(which != 'input' and which != 'output'):
			raise Exception("Can only delete port for 'input' and 'output'")

		if(which == "input"):
			return this._inputLink._delete(name)
		else: return this._outputLink._delete(name)

	def log(this, message):
		this.instance._log({"iface": this.iface, "message": message})

	# ToDo: remote-control PHP
	def syncOut(this, id, data): pass

	# To be overriden by module developer
	def imported(this, data): pass
	def update(this, cable): pass
	def request(this, cable): pass
	def destroy(this): pass
	def init(this): pass
	def syncIn(this, id, data): pass