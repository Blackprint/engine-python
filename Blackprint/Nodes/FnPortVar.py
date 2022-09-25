from ..Port.PortFeature import Port
from ..Types import Types
from ..Node import Node
from ..Interface import Interface
from ..Nodes.Enums import Enums
from ..Internal import registerNode, registerInterface

@registerNode('BP/FnVar/Input')
class FnVarInput(Node):
	output = {}

	def __init__(this, instance):
		Node.__init__(this, instance)

		iface = this.setInterface('BPIC/BP/FnVar/Input')

		# Specify data field from here to make it enumerable and exportable
		iface.data = {"name": ''}
		iface.title = 'FnInput'

		iface._enum = Enums.BPFnVarInput
		iface._dynamicPort = True # Port is initialized dynamically

	def imported(this, data):
		if(this.routes != None):
			this.routes.disabled = True

	def request(this, cable):
		iface = this.iface

		# This will trigger the port to request from outside and assign to this node's port
		this.output['Val'](iface._parentFunc.node.input[iface.data['name']]())

@registerNode('BP/FnVar/Output')
class FnVarOutput(Node):
	input = {}
	def __init__(this, instance):
		Node.__init__(this, instance)

		iface = this.setInterface('BPIC/BP/FnVar/Output')

		# Specify data field from here to make it enumerable and exportable
		iface.data = {"name": ''}
		iface.title = 'FnOutput'

		iface._enum = Enums.BPFnVarOutput
		iface._dynamicPort = True # Port is initialized dynamically

	def update(this, cable):
		id = this.iface.data['name']
		this.refOutput[id](this.ref.Input["Val"]())

class BPFnVarInOut(Interface):
	def imported(this, data):
		if(not data['name']): raise Exception("Parameter 'name' is required")
		this.data['name'] = data['name']
		this._parentFunc = this.node.instance._funcMain


@registerInterface('BPIC/BP/FnVar/Input')
class FnVarInputIface(BPFnVarInOut):
	def __init__(this, node):
		BPFnVarInOut.__init__(this, node)
		this.type = 'bp-fnvar-input'

	def imported(this, data):
		BPFnVarInOut.imported(this, data)
		ports = this._parentFunc.ref.IInput
		node = this.node

		this._proxyIface = this._parentFunc._proxyInput.iface

		# Create temporary port if the main function doesn't have the port
		name = data['name']
		if(name not in ports):
			iPort = node.createPort('output', 'Val', Types.Any)
			proxyIface = this._proxyIface

			# Run when this node is being connected with other node
			def onConnect(cable, port):
				del iPort.onConnect
				proxyIface.off("_add.[name]", this._waitPortInit)
				this._waitPortInit = None

				cable.disconnect()
				node.deletePort('output', 'Val')

				portName = {"name": name}
				portType = getFnPortType(port, 'input', this._parentFunc, portName)
				newPort = node.createPort('output', 'Val', portType)
				newPort._name = portName
				newPort.connectPort(port)

				proxyIface.addPort(port, name)
				this._addListener()
				return True

			iPort.onConnect = onConnect

			# Run when main node is the missing port
			def _waitPortInit(port):
				del iPort.onConnect
				this._waitPortInit = None

				backup = []
				cables = this.output['Val'].cables
				for cable in cables:
					backup.append(cable.input)

				node.deletePort('output', 'Val')

				portType = getFnPortType(port, 'input', this._parentFunc, port._name)
				newPort = node.createPort('output', 'Val', portType)
				this._addListener()

				for val in backup:
					newPort.connectPort(val)

			this._waitPortInit = _waitPortInit

			proxyIface.once("_add.[name]", this._waitPortInit)

		else:
			if('Val' not in this.output):
				port = ports[name]
				portType = getFnPortType(port, 'input', this._parentFunc, port._name)
				node.createPort('output', 'Val', portType)

			this._addListener()

	def _addListener(this):
		port = this._proxyIface.output[this.data['name']]

		if(port.feature == Port.Trigger):
			def _listener():
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

	
				this.ref.Output['Val'](port.value)

			this._listener = _listener
			port.on('value', _listener)

	def destroy(this):
		BPFnVarInOut.destroy(this)
		if(this._listener == None): return

		port = this._proxyIface.output[this.data['name']]
		if(port.feature == Port.Trigger):
			port.off('call', this._listener)
		else: port.off('value', this._listener)

@registerInterface('BPIC/BP/FnVar/Output')
class FnVarOutputIface(BPFnVarInOut):
	def __init__(this, node):
		BPFnVarInOut.__init__(this, node)
		this.type = 'bp-fnvar-output'

	def imported(this, data):
		BPFnVarInOut.imported(this, data)
		ports = this._parentFunc.ref.IOutput
		node = this.node

		node.refOutput = this._parentFunc.ref.Output

		# Create temporary port if the main function doesn't have the port
		name = data['name']
		if(name not in ports):
			iPort = node.createPort('input', 'Val', Types.Any)
			proxyIface = this._parentFunc._proxyOutput.iface

			# Run when this node is being connected with other node
			def onConnect(cable, port):
				del iPort.onConnect
				proxyIface.off("_add.:name}", this._waitPortInit)
				this._waitPortInit = None

				cable.disconnect()
				node.deletePort('input', 'Val')

				portName = {"name": name}
				portType = getFnPortType(port, 'output', this._parentFunc, portName)
				newPort = node.createPort('input', 'Val', portType)
				newPort._name = portName
				newPort.connectPort(port)

				proxyIface.addPort(port, name)
				return True
			
			iPort.onConnect = onConnect

			# Run when main node is the missing port
			def _waitPortInit(port):
				del iPort.onConnect
				this._waitPortInit = None

				backup = []
				cables = this.input['Val'].cables
				for cable in cables:
					backup.append(cable.output)

				node.deletePort('input', 'Val')

				portType = getFnPortType(port, 'output', this._parentFunc, port._name)
				newPort = node.createPort('input', 'Val', portType)

				for value in backup:
					newPort.connectPort(value)

			this._waitPortInit = _waitPortInit
			proxyIface.once("_add.[name]", this._waitPortInit)

		else:
			port = ports[name]
			portType = getFnPortType(port, 'output', this._parentFunc, port._name)
			node.createPort('input', 'Val', portType)


def getFnPortType(port, which, parentNode, ref):
	if(port.feature == Port.Trigger):
		if(which == 'input'): # Function Input (has output port inside, and input port on main node):
			return Types.Function
		else: return Port.Trigger(parentNode.output[ref.name]._callAll)

	else: return port.feature != port.feature(port.type) if None else port.type