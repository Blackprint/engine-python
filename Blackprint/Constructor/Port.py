from types import FunctionType

from ..Internal import EvCableError, EvPortValue
from ..Constructor.CustomEvent import CustomEvent
from ..Constructor.Cable import Cable
from ..Port.PortFeature import Port as PortFeature
from ..Types import Types
from ..Nodes.Enums import Enums
from ..Utils import Utils

from typing import TYPE_CHECKING
if TYPE_CHECKING:
	from ..Interface import Interface

class Port(CustomEvent):
	name: str
	type = None
	cables: list[Cable] = None
	source: str
	iface: 'Interface' = None
	default = None
	value = None
	feature = None
	onConnect = None
	splitted = False
	struct = None
	allowResync = False # Retrigger connected node's .update when the output value is similar

	_sync = True
	_ghost = False
	_name = None
	_callAll = None
	_cache = None
	_func = None
	_hasUpdate = False
	_hasUpdateCable = None
	_node = None

	def __init__(this, portName, type, def_, which, iface, feature):
		CustomEvent.__init__(this)

		this.name = portName
		this.type = type
		this.source = which
		this.iface = iface
		this.cables = []
		this._node = iface.node

		if(feature == False):
			this.default = def_
			return

		# this.value
		if(feature == PortFeature.Trigger):
			def callb():
				def_(this)

				if(this.iface._enum != Enums.BPFnMain):
					this.iface.node.routes.routeOut()

			this.default_ = callb
			this.default = lambda: Utils.runAsync(callb())

		elif(feature == PortFeature.StructOf):
			this.struct = def_
		else: this.default = def_

		this.feature = feature

	def _getPortFeature(this):
		if(this.feature == PortFeature.ArrayOf):
			return PortFeature.ArrayOf(this.type)

		elif(this.feature == PortFeature.Default):
			return PortFeature.Default(this.type, this.default)

		elif(this.feature == PortFeature.Trigger):
			return PortFeature.Trigger(this._func)

		elif(this.feature == PortFeature.Union):
			return PortFeature.Union(this.type)

		raise Exception("Port feature not recognized")

	def disconnectAll(this, hasRemote=False):
		cables = this.cables
		for cable in cables:
			if(hasRemote):
				cable._evDisconnected = True

			cable.disconnect()

	def createLinker(this):
		# Callable port
		if(this.source == 'output' and (this.type == FunctionType or this.type == Types.Route)):
			this._sync = False

			if(this.type == FunctionType):
				this._callAll = createCallablePort(this)
			else:
				this._callAll = createCallableRoutePort(this)

		# if(this.feature == PortFeature.Trigger):
		# 	return this.default

		# class PortLink already handle the linker

	# Only for output port
	def sync(this):
		# Check all connected cables, if any node need to synchronize
		cables = this.cables
		thisNode = this._node
		skipSync = this.iface.node.routes.out != None
		instance = thisNode.instance

		singlePortUpdate = False
		if(not thisNode._bpUpdating):
			singlePortUpdate = True
			thisNode._bpUpdating = True

		if(thisNode.routes.out != None
		   and thisNode.iface._enum == Enums.BPFnMain
		   and thisNode.iface.bpInstance.executionOrder.length != 0):
			skipSync = True

		for cable in cables:
			inp = cable.input
			if(inp == None): continue
			inp._cache = None

			inpIface = inp.iface
			temp = EvPortValue(inp, this, cable)
			inp.emit('value', temp)
			inpIface.emit('port.value', temp)

			if(skipSync == False and thisNode._bpUpdating):
				if(inp.feature == PortFeature.ArrayOf):
					inp._hasUpdate = True
					cable._hasUpdate = True
				else: inp._hasUpdateCable = cable

				if(inpIface._requesting == False):
					instance.executionOrder.add(inp._node)

			# Skip sync if the node has route cable
			if(skipSync or thisNode._bpUpdating): continue

			# print(f"\n4. {inp.name} = {inpIface.title}, {inpIface._requesting}")

			node = inpIface.node
			if(inpIface._requesting == False and len(node.routes.inp) == 0):
				Utils.runAsync(node._bpUpdate())

		if(singlePortUpdate):
			thisNode._bpUpdating = False
			Utils.runAsync(thisNode.instance.executionOrder.next())

	def disableCables(this, enable=False):
		cables = this.cables

		if(enable == True):
			for cable in cables:
				cable.disabled = 1
		elif(enable == False):
			for cable in cables:
				cable.disabled = 0
		else:
			for cable in cables:
				cable.disabled += enable

	def _cableConnectError(this, name, obj, severe=True):
		msg = f"Cable notify: {name}"
		iface = None
		port = None
		target = None

		if('iface' in obj):
			msg += f"\nIFace: {obj['iface'].namespace}"
			iface = obj['iface']

		if('port' in obj):
			msg += f"\nFrom port: {obj['port'].name} (iface: {obj['port'].iface.namespace})\n - Type: {obj['port'].source} ({obj['port'].type})"
			port = obj['port']

		if('target' in obj):
			msg += f"\nTo port: {obj['target'].name} (iface: {obj['target'].iface.namespace})\n - Type: {obj['target'].source} ({obj['target'].type})"
			target = obj['target']

		instance = this.iface.node.instance
		# print(msg)

		if(severe and instance.throwOnError):
			raise Exception(msg+"\n")

		instance.emit(name, EvCableError(iface, port, target, msg))

	def connectCable(this, cable: Cable):
		if(cable.isRoute):
			this._cableConnectError('cable.not_route_port', {
				"cable": cable,
				"port": this,
				"target": cable.owner
			})

			cable.disconnect()
			return False

		cableOwner = cable.owner

		if(cableOwner == this): # It's referencing to same port
			cable.disconnect()
			return False

		if((this.onConnect != None and this.onConnect(cable, cableOwner))
			or (cableOwner.onConnect != None and cableOwner.onConnect(cable, this))):
			return False

		# Remove cable if ...
		if((cable.source == 'output' and this.source != 'input') # Output source not connected to input
			or (cable.source == 'input' and this.source != 'output')  # Input source not connected to output
			# or (cable.source == 'property' and this.source != 'property')  # Property source not connected to property
		):
			this._cableConnectError('cable.wrong_pair', {
				"cable": cable,
				"port": this,
				"target": cableOwner
			})
			cable.disconnect()
			return False

		if(cableOwner.source == 'output'):
			if((this.feature == PortFeature.ArrayOf and not PortFeature.ArrayOf_validate(this.type, cableOwner.type))
			   or (this.feature == PortFeature.Union and not PortFeature.Union_validate(this.type, cableOwner.type))):
				this._cableConnectError('cable.wrong_type', {
					"cable": cable,
					"iface": this.iface,
					"port": cableOwner,
					"target": this
				})

				cable.disconnect()
				return False

		elif(this.source == 'output'):
			if((cableOwner.feature == PortFeature.ArrayOf and not PortFeature.ArrayOf_validate(cableOwner.type, this.type))
			   or (cableOwner.feature == PortFeature.Union and not PortFeature.Union_validate(cableOwner.type, this.type))):
				this._cableConnectError('cable.wrong_type', {
					"cable": cable,
					"iface": this.iface,
					"port": this,
					"target": cableOwner
				})

				cable.disconnect()
				return False

		# ToDo: recheck why we need to check if the constructor is a function
		isInstance = True
		if(cableOwner.type != this.type
		   and cableOwner.type == FunctionType
		   and this.type == FunctionType):
			if(cableOwner.source == 'output'):
				isInstance = issubclass(cableOwner.type, this.type)
			else: isInstance =  issubclass(this.type, cableOwner.type)

		# Remove cable if type restriction
		if(not isInstance or (
			   cableOwner.type == FunctionType and this.type != FunctionType
			or cableOwner.type != FunctionType and this.type == FunctionType
		)):
			this._cableConnectError('cable.wrong_type_pair', {
				"cable": cable,
				"port": this,
				"target": cableOwner
			})

			cable.disconnect()
			return False

		# Restrict connection between function input/output node with variable node
		# Connection to similar node function IO or variable node also restricted
		# These port is created on runtime dynamically
		if(this.iface._dynamicPort and cableOwner.iface._dynamicPort):
			this._cableConnectError('cable.unsupported_dynamic_port', {
				"cable": cable,
				"port": this,
				"target": cableOwner
			})

			cable.disconnect()
			return False

		sourceCables = cableOwner.cables

		# Remove cable if there are similar connection for the ports
		for _cable in sourceCables:
			if(_cable in this.cables):
				this._cableConnectError('cable.duplicate_removed', {
					"cable": cable,
					"port": this,
					"target": cableOwner
				}, False)

				cable.disconnect()
				return False

		# Put port reference to the cable
		cable.target = this

		if(cable.target.source == 'input'):
			# @var Port 
			inp = cable.target
			out = cableOwner

		else:
			# @var Port 
			inp = cableOwner
			out = cable.target

		# Remove old cable if the port not support array
		if(inp.feature != PortFeature.ArrayOf and inp.type != FunctionType):
			cables = inp.cables # Cables in input port
			cableLen = len(cables)

			if(cableLen != 0):
				temp = cables[0]

				if(temp == cable and cableLen == 1): pass
				else:
					temp = cables[1]

					if(temp != None):
						inp._cableConnectError('cable.replaced', {
							"cable": cable,
							"oldCable": temp,
							"port": inp,
							"target": out,
						}, False)
						temp.disconnect()

		# Connect this cable into port's cable list
		this.cables.append(cable)
		# cable.connecting()
		cable._connected()

		return True

	def connectPort(this, port: 'Port'):
		cable = Cable(port, this)
		if(port._ghost): cable._ghost = True

		port.cables.append(cable)
		return this.connectCable(cable)

def createCallablePort(port):
	def loop():
		cables = port.cables
		for cable in cables:
			target = cable.input
			if(target == None):
				continue

			if(target._name != None):
				target.iface._funcMain.node.output[target._name.name]()
			else: target.iface.input[target.name].default_()

		port.emit('call')

	def callable():
		if(port.iface.node.disablePorts): return
		Utils.runAsync(loop())

	return callable

def createCallableRoutePort(port):
	port.isRoute = True
	port.iface.node.routes.disableOut = True

	def callable():
		cable = port.cables[0]
		if(cable == None): return

		cable.input.routeIn()

	return callable