from ..Constructor.CustomEvent import CustomEvent
from ..Constructor.Cable import Cable
from ..Port.PortFeature import Port
from ..Types import Types
from ..Nodes.Enums import Enums

class Port(CustomEvent):
	name: str
	type = None
	cables = []
	source: str
	iface = None
	default = None
	value = None
	sync = False
	feature = None
	onConnect = False
	splitted = False
	struct = None
	allowResync = False # Retrigger connected node's .update when the output value is similar

	_ghost = False
	_name = None
	_callAll = None
	_cache = None
	_func = None

	def __init__(this, portName, type, def_, which, iface, feature):
		this.name = portName
		this.type = type
		this.source = which
		this.iface = iface

		if(feature == False):
			this.default = def_
			return

		# this.value
		if(feature == Port.Trigger):
			def callb():
				def_(this)
				this.iface.node.routes.routeOut()

			this.default = callb

		elif(feature == Port.StructOf):
			this.struct = def_
		else: this.default = def_

		this.feature = feature

	def _getPortFeature(this):
		if(this.feature == Port.ArrayOf):
			return Port.ArrayOf(this.type)

		elif(this.feature == Port.Default):
			return Port.Default(this.type, this.default)

		elif(this.feature == Port.Trigger):
			return Port.Trigger(this._func)

		elif(this.feature == Port.Union):
			return Port.Union(this.type)

		raise Exception("Port feature not recognized")

	def disconnectAll(this, hasRemote=False):
		cables = this.cables
		for cable in cables:
			if(hasRemote):
				cable._evDisconnected = True

			cable.disconnect()

	def createLinker(this):
		# Callable port
		if(this.source == 'output' and (this.type == Types.Function or this.type == Types.Route)):
			this.sync = False

			if(this.type == Types.Function):
				this._callAll = createCallablePort(this)
			else:
				this._callAll = createCallableRoutePort(this)

		# if(this.feature == Port.Trigger):
		# 	return this.default

		# class PortLink already handle the linker

	# Only for output port
	def sync(this):
		cables = this.cables
		skipSync = this.iface.node.routes.out != None

		for cable in cables:
			inp = cable.input
			if(inp == None): continue
			inp._cache = None
			
			temp = {"port": inp, "target": this, "cable": cable}
			inpIface = inp.iface

			inp.emit('value', temp)
			inpIface.emit('port.value', temp)

			# Skip sync if the node has route cable
			if(skipSync): continue

			# echo "\n4. [inp.name] = [inpIface.title], [inpIface._requesting]"

			node = inpIface.node
			if(inpIface._requesting == False and len(node.routes.inp) == 0):
				node.update(cable)

				if(inpIface._enum != Enums.BPFnMain):
					node.routes.routeOut()

				else:
					inpIface._proxyInput.routes.routeOut()

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
		msg = "Cable notify: [name]"
		if('iface' in obj): msg += "\nIFace: [obj['iface'].namespace]"

		if('port' in obj):
			msg += "\nFrom port: [obj['port'].name] (iface: [obj['port'].iface.namespace])\n - Type: [obj['port'].source] ([obj['port'].type.name])"

		if('target' in obj):
			msg += "\nTo port: [obj['target'].name] (iface: [obj['target'].iface.namespace])\n - Type: [obj['target'].source] ([obj['target'].type.name])"

		obj['message'] = msg
		instance = this.iface.node.instance

		if(severe and instance.throwOnError):
			raise Exception(msg+"\n\n")

		instance.emit(name, obj)

	def connectCable(this, cable: Cable):
		if(cable.isRoute):
			this._cableConnectError('cable.not_route_port', {
				"cable": cable,
				"port": this,
				"target": cable.owner
			})

			cable.disconnect()
			return False

		if(cable.owner == this): # It's referencing to same port
			cable.disconnect()
			return False

		if((this.onConnect != None and this.onConnect(cable, cable.owner))
			or (cable.owner.onConnect != None and (cable.owner.onConnect)(cable, this))):
			return False

		# Remove cable if ...
		if((cable.source == 'output' and this.source != 'input') # Output source not connected to input
			or (cable.source == 'input' and this.source != 'output')  # Input source not connected to output
			# or (cable.source == 'property' and this.source != 'property')  # Property source not connected to property
		):
			this._cableConnectError('cable.wrong_pair', {
				"cable": cable,
				"port": this,
				"target": cable.owner
			})
			cable.disconnect()
			return False

		if(cable.owner.source == 'output'):
			if((this.feature == Port.ArrayOf and not Port.ArrayOf_validate(this.type, cable.owner.type))
			   or (this.feature == Port.Union and not Port.Union_validate(this.type, cable.owner.type))):
				this._cableConnectError('cable.wrong_type', {
					"cable": cable,
					"iface": this.iface,
					"port": cable.owner,
					"target": this
				})

				cable.disconnect()
				return False

		elif(this.source == 'output'):
			if((cable.owner.feature == Port.ArrayOf and not Port.ArrayOf_validate(cable.owner.type, this.type))
			   or (cable.owner.feature == Port.Union and not Port.Union_validate(cable.owner.type, this.type))):
				this._cableConnectError('cable.wrong_type', {
					"cable": cable,
					"iface": this.iface,
					"port": this,
					"target": cable.owner
				})

				cable.disconnect()
				return False

		# ToDo: recheck why we need to check if the constructor is a function
		isInstance = True
		if(cable.owner.type != this.type
		   and cable.owner.type == Types.Function
		   and this.type == Types.Function):
			if(cable.owner.source == 'output'):
				isInstance = issubclass(cable.owner.type, this.type)
			else: isInstance =  issubclass(this.type, cable.owner.type)

		# Remove cable if type restriction
		if(not isInstance or (
			   cable.owner.type == Types.Function and this.type != Types.Function
			or cable.owner.type != Types.Function and this.type == Types.Function
		)):
			this._cableConnectError('cable.wrong_type_pair', {
				"cable": cable,
				"port": this,
				"target": cable.owner
			})

			cable.disconnect()
			return False

		# Restrict connection between function input/output node with variable node
		# Connection to similar node function IO or variable node also restricted
		# These port is created on runtime dynamically
		if(this.iface._dynamicPort and cable.owner.iface._dynamicPort):
			this._cableConnectError('cable.unsupported_dynamic_port', {
				"cable": cable,
				"port": this,
				"target": cable.owner
			})

			cable.disconnect()
			return False

		sourceCables = cable.owner.cables

		# Remove cable if there are similar connection for the ports
		for _cable in sourceCables:
			if(_cable in this.cables):
				this._cableConnectError('cable.duplicate_removed', {
					"cable": cable,
					"port": this,
					"target": cable.owner
				}, False)

				cable.disconnect()
				return False

		# Put port reference to the cable
		cable.target = this

		if(cable.target.source == 'input'):
			# @var Port 
			inp = cable.target
			out = cable.owner

		else:
			# @var Port 
			inp = cable.owner
			out = cable.target

		# Remove old cable if the port not support array
		if(inp.feature != Port.ArrayOf and inp.type != Types.Function):
			cables = inp.cables # Cables in input port

			if(len(cables) != 0):
				temp = cables[0]

				if(temp == cable):
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

	def connectPort(this, port: Port):
		cable = Cable(port, this)
		if(port._ghost): cable._ghost = True

		port.cables.append(cable)
		return this.connectCable(cable)

def createCallablePort(port):
	def callable():
		if(port.iface.node.disablePorts): return

		cables = port.cables
		for cable in cables:
			target = cable.input
			if(target == None):
				continue

			if(target._name != None):
				target.iface._parentFunc.node.output[target._name.name]()
			else: target.iface.input[target.name].default()

		port.emit('call')

	return callable

def createCallableRoutePort(port):
	port.isRoute = True
	port.iface.node.routes.disableOut = True

	def callable():
		cable = port.cables[0]
		if(cable == None): return

		cable.input.routeIn(cable)

	return callable