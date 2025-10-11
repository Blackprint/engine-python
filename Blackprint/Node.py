import asyncio
import inspect
from .RoutePort import RoutePort
from .Constructor.CustomEvent import CustomEvent
from .Constructor.Port import Port as PortClass
from .Constructor.References import References
from .Constructor.PortLink import PortLink
from .Interface import Interface
from .Internal import Internal
from .Nodes.Enums import Enums
from .Types import Types
from .Port.PortFeature import Port as PortFeature

from typing import TYPE_CHECKING
if TYPE_CHECKING:
	from .Engine import Engine

class Node(CustomEvent):
	output: PortLink = None
	input: PortLink = None
	disablePorts = False
	partialUpdate = False

	# If enabled, syncIn will have 3 parameter, and syncOut will be send to related node in other function instances
	allowSyncToAllFunction = False
	iface: Interface = None
	routes: RoutePort = None
	ref: References = None

	# static
	type = None
	interfaceSync = None
	interfaceDocs = None

	_bpUpdating = False
	bpFunction = None
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

		if(type == None):
			raise Exception("Type is required for creating new port")

		if(not isinstance(name, str)):
			name = str(name)

		if(
			# Types
			type == Types.Slot or
			type == Types.Any or
			type == Types.Slot or
			type == Types.Route or
			type == Types.Trigger or

			# PortFeature
			(isinstance(type, dict) and 'feature' in type and (
				type['feature'] == PortFeature.ArrayOf or
				type['feature'] == PortFeature.Default or
				type['feature'] == PortFeature.Trigger or
				type['feature'] == PortFeature.Union or
				type['feature'] == PortFeature.StructOf
			)) or

			# Check if type is a class (built-in or custom)
			inspect.isclass(type)
		  ):

			if(which == "input"):
				ret = this.input._add(name, type)
			else: ret = this.output._add(name, type)

			return ret

		print("Get type:")
		print(type)
		raise Exception("Type must be a class object or from Blackprint.Port.{feature}")

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

		if(not isinstance(name, str)):
			name = str(name)

		ret = this[which]._delete(name)

		return ret

	def log(this, message):
		this.instance._log({"iface": this.iface, "message": message})

	async def _bpUpdate(this, cable=None):
		thisIface = this.iface
		isMainFuncNode = thisIface._enum == Enums.BPFnMain
		ref = this.instance.executionOrder

		if(this.update != None):
			this._bpUpdating = True
			try:
				temp = this.update(cable)
				if(asyncio.iscoroutine(temp)): await temp # Performance optimization
			finally:
				this._bpUpdating = False
			this.iface.emit('updated')

		if(this.routes.out == None):
			if(isMainFuncNode and hasattr(thisIface, '_proxyInput') and thisIface._proxyInput.routes.out != None):
				await thisIface._proxyInput.routes.routeOut()
		else:
			if(not isMainFuncNode):
				await this.routes.routeOut()
			else:
				if(hasattr(thisIface, '_proxyInput')):
					await thisIface._proxyInput.routes.routeOut()

		await ref.next()

	def _syncToAllFunction(this, id, data):
		parentInterface = this.instance.parentInterface
		if(parentInterface == None): return # This is not in a function node

		list = parentInterface.node.bpFunction.used
		nodeIndex = this.iface.i
		namespace = parentInterface.namespace

		for iface in list:
			if(iface == parentInterface): continue # Skip self
			target = iface.bpInstance.ifaceList[nodeIndex]

			if(target == None):
				# console.log(12, iface.bpInstance.ifaceList, target, nodeIndex, this.iface)
				raise Exception(f"Target node was not found on other function instance, maybe the node was not correctly synced/saved? ({namespace.replace('BPI/F/', '')});")
			target.node.syncIn(id, data, False)

	def syncOut(this, id, data, force=False):
		if(this.allowSyncToAllFunction): this._syncToAllFunction(id, data)

		instance = this.instance
		if(instance.rootInstance != None):
			instance.rootInstance = instance.rootInstance # Ensure rootInstance is set

		remote = instance._remote
		if(remote != None):
			remote.nodeSyncOut(this, id, data, force)

	# To be overriden by module developer
	def init(this): pass
	def imported(this, data): pass
	def update(this, cable): pass
	def request(this, cable): pass
	def initPorts(this, data): pass
	def destroy(this): pass
	def syncIn(this, id, data, isRemote=False): pass
	def notifyEditorDataChanged(this): pass # Do nothing, this only required for Blackprint.Sketch