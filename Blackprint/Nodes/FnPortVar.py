from ..Port.PortFeature import Port
from ..Types import Types
from ..Node import Node
from ..Interface import Interface
from ..Nodes.Enums import Enums
from ..Internal import registerNode, registerInterface

class PortName():
	def __init__(this, name):
		this.name: str = name

@registerNode('BP/FnVar/Input')
class FnVarInput(Node):
	output = {}
	# @var FnVarInputIface
	iface: 'FnVarInputIface' = None

	def __init__(this, instance):
		Node.__init__(this, instance)

		iface = this.setInterface('BPIC/BP/FnVar/Input')

		# Specify data field from here to make it enumerable and exportable
		iface.data = {"name": ''}
		iface.title = 'FnInput'

		iface._enum = Enums.BPFnVarInput

	def imported(this, data):
		if(this.routes != None):
			this.routes.disabled = True

	def request(this, cable):
		iface = this.iface

		# This will trigger the port to request from outside and assign to this node's port
		this.output['Val'] = iface._funcMain.node.input[iface.data['name']]

	def destroy(this):
		iface = this.iface
		if(iface._listener == None): return

		port = iface._proxyIface.output[iface.data['name']]
		if(port.feature == Port.Trigger):
			port.off('call', iface._listener)
		else: port.off('value', iface._listener)

@registerNode('BP/FnVar/Output')
class FnVarOutput(Node):
	input = {}
	refOutput = None
	def __init__(this, instance):
		Node.__init__(this, instance)

		iface = this.setInterface('BPIC/BP/FnVar/Output')

		# Specify data field from here to make it enumerable and exportable
		iface.data = {"name": ''}
		iface.title = 'FnOutput'

		iface._enum = Enums.BPFnVarOutput

	def update(this, cable):
		iface = this.iface
		id = iface.data['name']
		this.refOutput[id] = this.ref.Input["Val"]

		mainNodeIFace = iface._funcMain
		proxyOutputNode = mainNodeIFace._proxyOutput

		# Also update the cache on the proxy node
		proxyOutputNode.ref.IInput[id]._cache = this.ref.Input['Val']

		# If main node has route and the output proxy doesn't have input route
		# Then trigger out route on the main node
		mainNodeRoutes = mainNodeIFace.node.routes
		if(mainNodeRoutes.out != None and len(proxyOutputNode.routes.inp) == 0):
			mainNodeRoutes.routeOut()

class BPFnVarInOut(Interface):
	_dynamicPort = True # Port is initialized dynamically

	def imported(this, data):
		if('name' not in data or data['name'] == ''): raise Exception("Parameter 'name' is required")
		this.data['name'] = data['name']
		this._funcMain = this.node.instance._funcMain


@registerInterface('BPIC/BP/FnVar/Input')
class FnVarInputIface(BPFnVarInOut):
	_listener = None
	_proxyIface = None
	_waitPortInit = None

	def __init__(this, node):
		BPFnVarInOut.__init__(this, node)
		this.type = 'bp-fnvar-input'

	def imported(this, data):
		BPFnVarInOut.imported(this, data)
		ports = this._funcMain.ref.IInput
		node = this.node

		this._proxyIface = this._funcMain._proxyInput.iface

		# Create temporary port if the main function doesn't have the port
		name = data['name']
		if(name not in ports):
			iPort = node.createPort('output', 'Val', Types.Slot)
			proxyIface = this._proxyIface

			# Run when this node is being connected with other node
			def onConnect(cable, port):
				# Skip port with feature: ArrayOf
				if(port.feature == Port.ArrayOf): return

				iPort.onConnect = None
				proxyIface.off(f"_add.{name}", this._waitPortInit)
				this._waitPortInit = None

				portName = PortName(name)
				portType = getFnPortType(port, 'input', this, portName)
				iPort.assignType(portType)
				iPort._name = portName

				proxyIface.addPort(port, name)
				tPort = port if cable.owner == iPort else iPort
				tPort.connectCable(cable)

				this._addListener()
				return True

			iPort.onConnect = onConnect

			# Run when main node is the missing port
			def _waitPortInit(port):
				# Skip port with feature: ArrayOf
				if(port.feature == Port.ArrayOf): return

				iPort.onConnect = None
				this._waitPortInit = None

				portType = getFnPortType(port, 'input', this, port._name)
				iPort.assignType(portType)
				this._addListener()

			this._waitPortInit = _waitPortInit

			proxyIface.once(f"_add.{name}", this._waitPortInit)

		else:
			if('Val' not in this.output):
				port = this._funcMain._proxyInput.iface.output[name]
				portType = getFnPortType(port, 'input', this, port._name)
				newPort = node.createPort('output', 'Val', portType)
				newPort._name = port._name

			this._addListener()

	def _addListener(this):
		port = this._proxyIface.output[this.data['name']]

		if(port.type == Types.Trigger):
			def _listener(ev):
				this.ref.Output['Val']()

			this._listener = _listener
			port.on('call', _listener)

		else:
			def _listener(dat):
				port = dat.port

				if(port.iface.node.routes.out != None):
					Val = this.ref.IOutput['Val']
					Val.value = port.value # Change value without trigger node.update

					list = Val.cables
					for temp in list:
						# Clear connected cable's cache
						temp.input._cache = None

					return

				this.ref.Output['Val'] = port.value

			this._listener = _listener
			port.on('value', _listener)

@registerInterface('BPIC/BP/FnVar/Output')
class FnVarOutputIface(BPFnVarInOut):
	_waitPortInit = None
	type = None
	node: 'FnVarOutput' = None

	def __init__(this, node):
		BPFnVarInOut.__init__(this, node)
		this.type = 'bp-fnvar-output'

	def imported(this, data):
		BPFnVarInOut.imported(this, data)
		ports = this._funcMain.ref.IOutput
		node = this.node

		node.refOutput = this._funcMain.ref.Output

		# Create temporary port if the main function doesn't have the port
		name = data['name']
		if(name not in ports):
			iPort = node.createPort('input', 'Val', Types.Slot)
			proxyIface = this._funcMain._proxyOutput.iface

			# Run when this node is being connected with other node
			def onConnect(cable, port):
				# Skip port with feature: ArrayOf
				if(port.feature == Port.ArrayOf): return

				iPort.onConnect = None
				proxyIface.off(f"_add.{name}", this._waitPortInit)
				this._waitPortInit = None

				portName = PortName(name)
				portType = getFnPortType(port, 'output', this, portName)
				iPort.assignType(portType)
				iPort._name = portName

				proxyIface.addPort(port, name)
				tPort = port if cable.owner == iPort else iPort
				tPort.connectCable(cable)
				return True
			
			iPort.onConnect = onConnect

			# Run when main node is the missing port
			def _waitPortInit(port):
				# Skip port with feature: ArrayOf
				if(port.feature == Port.ArrayOf): return

				iPort.onConnect = None
				this._waitPortInit = None

				portType = getFnPortType(port, 'output', this, port._name)
				iPort.assignType(portType)

			this._waitPortInit = _waitPortInit
			proxyIface.once(f"_add.{name}", this._waitPortInit)

		else:
			port = this._funcMain._proxyOutput.iface.input[name]
			portType = getFnPortType(port, 'output', this, port._name)
			newPort = node.createPort('input', 'Val', portType)
			newPort._name = port._name

	def _recheckRoute(this):
		if(this.input.Val.type != Types.Trigger): return

		routes = this.node.routes
		routes.disableOut = True
		routes.noUpdate = True

def _Dummy_PortTrigger_():
	raise Exception("This can't be called")

_Dummy_PortTrigger = Port.Trigger(_Dummy_PortTrigger_)

def getFnPortType(port, which, parentNode, ref):
	if(port.feature == Port.Trigger or port.type == Types.Trigger):
		# Function Input (has output port inside, and input port on main node):
		if(which == 'input'):
			return Types.Trigger
		else: return _Dummy_PortTrigger
	# Skip ArrayOf port feature, and just use the type
	elif(port.feature == Port.ArrayOf):
		return port.type
	elif(port._isSlot):
		raise Exception("Function node's input/output can't use port from an lazily assigned port type (Types.Slot)")
	else: return port._config