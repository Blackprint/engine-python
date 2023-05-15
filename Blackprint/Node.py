import asyncio
from .RoutePort import RoutePort
from .Constructor.CustomEvent import CustomEvent
from .Constructor.Port import Port as PortClass
from .Constructor.References import References
from .Constructor.PortLink import PortLink
from .Interface import Interface
from .Internal import Internal
from .Nodes.Enums import Enums

from typing import TYPE_CHECKING
if TYPE_CHECKING:
	from .Engine import Engine

class Node(CustomEvent):
	output: PortLink = None
	input: PortLink = None
	disablePorts = False
	partialUpdate = False
	iface: Interface = None
	routes: RoutePort = None
	ref: References = None

	# static
	type = None
	interfaceSync = None

	_bpUpdating = False
	_funcInstance = None
	_contructed = True

	# For remote control
	_syncronizing = None
	syncThrottle = 0
	_syncWait = None
	_syncHasWait = None

	def __init__(this, instance):
		CustomEvent.__init__(this)
		this.instance: 'Engine' = instance

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
		if(this.instance._locked_):
			raise Exception("This instance was locked")

		if(which != 'input' and which != 'output'):
			raise Exception("Can only create port for 'input' and 'output'")

		if(which == "input"):
			return this.input._add(name, type)
		else: return this.output._add(name, type)

	def renamePort(this, which, name, to):
		if(this.instance._locked_):
			raise Exception("This instance was locked")

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
		if(this.instance._locked_):
			raise Exception("This instance was locked")

		if(which != 'input' and which != 'output'):
			raise Exception("Can only delete port for 'input' and 'output'")

		if(which == "input"):
			return this.input._delete(name)
		else: return this.output._delete(name)

	def log(this, message):
		this.instance._log({"iface": this.iface, "message": message})

	def _bpUpdate(this):
		thisIface = this.iface
		isMainFuncNode = thisIface._enum == Enums.BPFnMain
		ref = this.instance.executionOrder

		this._bpUpdating = True
		cour = this.update(None)
		if(asyncio.iscoroutine(cour)): asyncio.run(cour)
		this._bpUpdating = False
		this.iface.emit('updated')

		if(this.routes.out == None):
			if(isMainFuncNode and thisIface.node.routes.out != None):
				thisIface.node.routes.routeOut()
				ref.next()
			else: ref.next()
		else:
			if(not isMainFuncNode):
				this.routes.routeOut()
			else: thisIface._proxyInput.routes.routeOut()

			ref.next()

	def syncOut(this, id, data):
		if(this.instance._remote != None):
			this.instance._remote.BpSyncOut(this, id, data)

	# To be overriden by module developer
	def init(this): pass
	def imported(this, data): pass
	def update(this, cable): pass
	def request(this, cable): pass
	def initPorts(this, data): pass
	def destroy(this): pass
	def syncIn(this, id, data): pass