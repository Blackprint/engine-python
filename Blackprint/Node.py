from Blackprint.RoutePort import RoutePort
from .Constructor.CustomEvent import CustomEvent
from .Constructor.Port import Port as PortClass
from .Constructor.References import References
from .Constructor.PortLink import PortLink
from .Interface import Interface
from .Internal import Internal

from typing import TYPE_CHECKING
if TYPE_CHECKING:
	from .Engine import Engine

class Node(CustomEvent):
	output: PortLink = None
	input: PortLink = None
	disablePorts = False

	def __init__(this, instance):
		CustomEvent.__init__(this)

		this.iface: Interface = None
		this.instance: 'Engine' = instance
		this.routes: RoutePort = None
		this.ref: References = None

		this._funcInstance = None
		this._contructed = True

	def setInterface(this, namespace='BP/default'):
		if(this.iface != None):
			raise Exception('node.setInterface() can only be called once')

		if(this._contructed == False):
			raise Exception("Make sure you have call 'Node.__init__(instance);' when constructing nodes before '.setInterface'")

		if(namespace not in Internal.interface):
			raise Exception(f"Node interface for '[{namespace}]' was not found, maybe .registerInterface() haven't being called?")

		iface = Internal.interface[namespace](this)
		this.iface = iface

		return iface

	def createPort(this, which, name, type):
		if(which != 'input' and which != 'output'):
			raise Exception("Can only create port for 'input' and 'output'")

		if(which == "input"):
			return this.input._add(name, type)
		else: return this.output._add(name, type)

	def renamePort(this, which, name, to):
		iPort = this.iface[which]

		if(name not in iPort):
			raise Exception(f"{which} port with name '{name}' was not found")

		if(to in iPort):
			raise Exception(f"{which} port with name '{to}' already exist")

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
			return this.input._delete(name)
		else: return this.output._delete(name)

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