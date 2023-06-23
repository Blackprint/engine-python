import asyncio
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
	isRoute = False

	_sync = True
	_ghost = False
	_isSlot = False
	_name = None
	_call_ = None
	_callDef = None
	_cache = None
	_config = None
	_func = None
	_hasUpdate = False
	_hasUpdateCable = None
	_node = None
	_cable = None
	_calling = False

	def __init__(this, portName, type, def_, which, iface, feature):
		CustomEvent.__init__(this)

		this.name = portName
		this.type = type
		this.source = which
		this.iface = iface
		this.cables = []
		this._node = iface.node
		this._isSlot = type == Types.Slot

		if(feature == False):
			this.default = def_
			return

		# this.value
		if(feature == PortFeature.Trigger):
			# if(def == this._callAll): raise Exception("Logic error")

			this._callDef = def_
			this.default = lambda: Utils.runAsync(this._call())

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

	def _call(this, cable=None):
		iface = this.iface

		if(cable == None):
			if(this._cable == None):
				this._cable = Cable(this, this)

			cable = this._cable

		if(this._calling):
			input = cable.input
			output = cable.output
			raise Exception(f"Circular call stack detected:\nFrom: {output.iface.title}.{output.name}\nTo: {input.iface.title}.{input.name})")

		this._calling = cable._calling = True
		try:
			this._callDef(this)
		finally:
			this._calling = cable._calling = False

		if(iface._enum != Enums.BPFnMain):
			iface.node.routes.routeOut()

	def _callAll(this):
		if(this.type == Types.Route):
			cables = this.cables
			cable = cables[0]

			if(cable == None): return
			if(cable.hasBranch): cable = cables[1]

			# if(Blackprint.settings.visualizeFlow)
			# 	cable.visualizeFlow()

			if(cable.input == None): return
			cable.input.routeIn(cable)
		else:
			node = this.iface.node
			if(node.disablePorts): return
			executionOrder = node.instance.executionOrder

			for cable in this.cables:
				target = cable.input
				if(target == None): continue

				# if(Blackprint.settings.visualizeFlow and !executionOrder.stepMode)
				# 	cable.visualizeFlow()

				if(target._name != None):
					target.iface._funcMain.node.iface.output[target._name.name]._callAll()
				else:
					if(executionOrder.stepMode):
						executionOrder._addStepPending(cable, 2)
						continue

					target.iface.input[target.name]._call(cable)

			this.emit('call')

	def createLinker(this):
		# Callable port
		if(this.source == 'output' and (this.type == Types.Trigger or this.type == Types.Route)):
			# Disable sync
			this._sync = False

			if(this.type != Types.Trigger):
				this.isRoute = True
				this.iface.node.routes.disableOut = True

			return lambda: this._callAll()

		# "var prepare = " is in PortLink.php (offsetGet)

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

			if(inp._cache != None and instance.executionOrder.stepMode):
				inp._oldCache = inp._cache

			inpIface = inp.iface
			inpNode = inpIface.node
			temp = EvPortValue(inp, this, cable)
			inp.emit('value', temp)
			inpIface.emit('port.value', temp)

			nextUpdate = inpIface._requesting == False and len(inpNode.routes.inp) == 0
			if(skipSync == False and thisNode._bpUpdating):
				if(inpNode.partialUpdate):
					if(inp.feature == PortFeature.ArrayOf):
						inp._hasUpdate = True
						cable._hasUpdate = True
					else: inp._hasUpdateCable = cable

				if(nextUpdate):
					instance.executionOrder.add(inp._node, cable)

			# Skip sync if the node has route cable
			if(skipSync or thisNode._bpUpdating): continue

			# print(f"\n4. {inp.name} = {inpIface.title}, {inpIface._requesting}")

			if(nextUpdate): inpNode._bpUpdate()

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

		instance._emit(name, EvCableError(iface, port, target, msg))

	def assignType(this, type_):
		if(type_ == None): raise Exception("Can't set type with undefined")

		if(this.type != Types.Slot):
			print(this.type)
			raise Exception("Can only assign type to port with 'Slot' type, this port already has type")

		# Skip if the assigned type is also Slot type
		if(type_ == Types.Slot): return

		# Check current output value type
		if(this.value != None):
			gettype = type(this.value)
			pass_ = False

			if(isinstance(this.value, type_)): pass_ = True
			elif(type_ == Types.Any or type_ == gettype):
				pass_ = True

			if(pass_ == False): raise Exception("The output value of this port is not instance of type that will be assigned: {gettype.name} is not instance of {type.name}")

		# Check connected cable's type
		for cable in this.cables:
			inputPort = cable.input
			if(inputPort == None): continue

			portType = inputPort.type
			if(portType == Types.Any): 1 # pass
			elif(portType == type_): 1 # pass
			elif(portType == Types.Slot): 1 # pass
			elif(Types.isType(portType) or Types.isType(type_)):
				raise Exception("The target port's connection of this port is not instance of type that will be assigned: {portType.name} is not instance of {type_.name}")
			else:
				if(isinstance(type_, dict) and type_['type'] != None):
					clazz = type_['type']
				else: clazz = type_

				if(not issubclass(portType, clazz)):
					raise Exception(f"The target port's connection of this port is not instance of type that will be assigned: {portType} is not instance of {clazz}")

		if(isinstance(type_, dict) and 'feature' in type_):
			if(this.source == 'output'):
				if(type_['feature'] == PortFeature.Union):
					type_ = Types.Any
				elif(type_['feature'] == PortFeature.Trigger):
					type_ = type_['type']
				elif(type_['feature'] == PortFeature.ArrayOf):
					type_ = list
				elif(type_['feature'] == PortFeature.Default):
					type_ = type_['type']
			else:
				if(type_['type'] == None): raise Exception("Missing type for port feature")

				this.feature = type_['feature']
				this.type = type_['type']

				if(type_['feature'] == PortFeature.StructOf):
					this.struct = type_['value']
					# this.classAdd .= "BP-StructOf "

			# if(type.virtualType != None)
			# 	this.virtualType = type.virtualType
		else: this.type = type_

		# Trigger `connect` event for every connected cable
		for cable in this.cables:
			if(cable.disabled or cable.target == None): continue
			cable._connected()

		this._config = type_
		this.emit('type.assigned')

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
			   cableOwner.type == Types.Trigger and this.type != Types.Trigger
			or cableOwner.type != Types.Trigger and this.type == Types.Trigger
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
		if(inp.feature != PortFeature.ArrayOf and inp.type != Types.Trigger):
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