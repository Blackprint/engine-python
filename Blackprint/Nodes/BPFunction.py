from typing import Dict

from ..Port.PortFeature import Port
from ..Utils import Utils
from ..Interface import Interface
from ..Node import Node
from ..Types import Types
from ..Constructor.CustomEvent import CustomEvent
from ..Constructor.Port import Port as PortClass
from .BPVariable import VarScope, BPVariable
from .Enums import Enums
from ..Internal import registerNode, registerInterface
import re

# used for instance.createFunction
class BPFunction(CustomEvent): # <= _funcInstance
	variables: Dict[str, BPVariable] = {} # shared between function
	privateVars = [] # private variable (different from other function)

	input = {} # Port template
	output = {} # Port template
	node = None # Node constructor (Function)

	def __init__(this, id, options, instance):
		this.rootInstance = instance # root instance

		id = re.sub(r'[`~!@#$%^&*()\-_+={}\[\]:"|;\'\\\\,.\/<>?]+', '_', id)
		this.id = this.title = id
		# this.description = options['description'] ?? ''

		input = this.input
		output = this.output
		this.used = [] # [Interface, ...]

		# This will be updated if the function sketch was modified
		if(options['structure'] != None):
			this.structure = options['structure']
		else:
			this.structure = {
				'BP/Fn/Input': [{'i': 0}],
				'BP/Fn/Output': [{'i': 1}],
			}

		temp = this
		uniqId = 0

		def nodeContruct(instance):
			BPFunctionNode.Input = input
			BPFunctionNode.Output = output
			BPFunctionNode.namespace = id

			node = BPFunctionNode(instance)
			iface = node.iface

			instance._funcInstance = temp
			node._funcInstance = temp
			# iface.description = temp.description
			iface.title = temp.title
			uniqId += 1
			iface.uniqId = uniqId

			iface._prepare_(BPFunctionNode)
			return node

		this.node = nodeContruct


	def _onFuncChanges(this, eventName, obj, fromNode):
		list = this.used

		for iface_ in list:
			if(iface_.node == fromNode): continue

			nodeInstance = iface_._bpInstance
			nodeInstance.pendingRender = True # Force recalculation for cable position

			if(eventName == 'cable.connect' or eventName == 'cable.disconnect'):
				input = obj.cable.input
				output = obj.cable.output
				ifaceList = fromNode.iface._bpInstance.ifaceList

				# Skip event that also triggered when deleting a node
				if(input.iface._bpDestroy or output.iface._bpDestroy): continue

				inputIface = nodeInstance.ifaceList[Utils.findFromList(ifaceList, input.iface)]
				if(inputIface == None):
					raise Exception("Failed to get node input iface index")

				outputIface = nodeInstance.ifaceList[Utils.findFromList(ifaceList, output.iface)]
				if(outputIface == None):
					raise Exception("Failed to get node output iface index")

				if(inputIface.namespace != input.iface.namespace):
					print(inputIface.namespace+' != '+input.iface.namespace)
					raise Exception("Input iface namespace was different")

				if(outputIface.namespace != output.iface.namespace):
					print(outputIface.namespace+' != '+output.iface.namespace)
					raise Exception("Output iface namespace was different")

				if(eventName == 'cable.connect'):
					targetInput = inputIface.input[input.name]
					targetOutput = outputIface.output[output.name]

					if(targetInput == None):
						if(inputIface._enum == Enums.BPFnOutput):
							targetInput = inputIface.addPort(targetOutput, output.name)

						else: raise Exception("Output port was not found")

					if(targetOutput == None):
						if(outputIface._enum == Enums.BPFnInput):
							targetOutput = outputIface.addPort(targetInput, input.name)

						else: raise Exception("Input port was not found")

					targetInput.connectPort(targetOutput)

				elif(eventName == 'cable.disconnect'):
					cables = inputIface.input[input.name].cables
					outputPort = outputIface.output[output.name]

					for cable in cables:
						if(cable.output == outputPort):
							cable.disconnect()
							break

			elif(eventName == 'node.created'):
				iface = obj.iface
				nodeInstance.createNode(iface.namespace, {
					"data": iface.data
				})

			elif(eventName == 'node.delete'):
				index = Utils.findFromList(fromNode.iface._bpInstance.ifaceList, obj.iface)
				if(index == False):
					raise Exception("Failed to get node index")

				iface = nodeInstance.ifaceList[index]
				if(iface.namespace != obj.iface.namespace):
					print(iface.namespace+' '+obj.iface.namespace)
					raise Exception("Failed to delete node from other function instance")

				if(eventName == 'node.delete'):
					nodeInstance.deleteNode(iface)

	def createNode(this, instance, options):
		return instance.createNode(this.node, options)

	def createVariable(this, id, options):
		if(id in this.variables):
			raise Exception("Variable id already exist: id")

		# deepProperty

		temp = BPVariable(id, options)
		temp.funcInstance = this

		if(options['scope'] == VarScope.shared):
			this.variables[id] = temp
		else:
			temp2 = this.addPrivateVars(id)
			return temp2

		this.emit('variable.new', temp)
		this.rootInstance.emit('variable.new', temp)
		return temp

	def addPrivateVars(this, id):
		if(id not in this.privateVars):
			this.privateVars.append(id)

			temp = {"scope": VarScope.private, "id": id}
			this.emit('variable.new', temp)
			this.rootInstance.emit('variable.new', temp)

		else: return

		list = this.used
		for iface in list:
			vars = iface._bpInstance.variables
			vars[id] = BPVariable(id)

	def refreshPrivateVars(this, instance):
		vars = instance.variables

		list = this.privateVars
		for id in list:
			vars[id] = BPVariable(id)

	def renamePort(this, which, fromName, toName):
		main = this[which]
		main[toName] = main[fromName]
		del main[fromName]

		used = this.used
		proxyPort = which == 'input' if 'output' else 'output'

		for iface in used:
			iface.node.renamePort(which, fromName, toName)

			temp = which == iface._proxyOutput if 'output' else iface._proxyInput
			temp.iface[proxyPort][fromName]._name.name = toName
			temp.renamePort(proxyPort, fromName, toName)

			ifaces = iface.bpInstance.ifaceList
			for proxyVar in ifaces:
				if((which == 'output' and proxyVar.namespace != "BP/FnVar/Output")
					or (which == 'input' and proxyVar.namespace != "BP/FnVar/Input")):
					continue

				if(proxyVar.data.name != fromName): continue
				proxyVar.data.name = toName

				if(which == 'output'):
					proxyVar[proxyPort]['Val']._name.name = toName

	def destroy(this):
		map = this.used
		for iface in map:
			iface.node.instance.deleteNode(iface)

# Main function node
class BPFunctionNode(Node): # Main function node . BPI/F/:FunctionName}
	Input = None
	Output = None
	namespace = None

	type = 'function'
	def __init__(this, instance):
		Node.__init__(this, instance)
		iface = this.setInterface("BPIC/BP/Fn/Main")
		iface.type = 'function'
		iface._enum = Enums.BPFnMain

	# @var FnMain 
	iface = None

	def init(this):
		if(not this.iface._importOnce): this.iface._BpFnInit()

	def imported(this, data):
		instance = this._funcInstance
		instance.used.append(this.iface)

	def update(this, cable):
		iface = this.iface._proxyInput.iface
		Output = iface.node.output

		if(cable == None): # Triggered by port route
			IOutput = iface.output
			thisInput = this.input

			# Sync all port value
			for key, value in IOutput.items():
				if(value.type == Types.Function): continue
				Output[key](thisInput[key]())

			return

		# Update output value on the input node inside the function node
		Output[cable.input.name](cable.value())

	def destroy(this):
		used = this._funcInstance.used

		i = Utils.findFromList(used, this.iface)
		if(i != False): used.pop(i)

@registerNode('BP/Fn/Input')
class NodeInput(Node):
	Output = []
	def __init__(this, instance):
		Node.__init__(this, instance)

		iface = this.setInterface('BPIC/BP/Fn/Input')
		iface._enum = Enums.BPFnInput
		iface._proxyInput = True # Port is initialized dynamically

		funcMain = this.instance._funcMain
		iface._funcMain = funcMain
		funcMain._proxyInput = this

	def imported(this, data):
		input = this.iface._funcMain.node._funcInstance.input

		for key, value in input.items():
			this.createPort('output', key, value)

	def request(this, cable):
		name = cable.output.name

		# This will trigger the port to request from outside and assign to this node's port
		this.output[name](this.iface._funcMain.node.input[name]())

@registerNode('BP/Fn/Output')
class NodeOutput(Node):
	Input = []
	def __init__(this, instance):
		Node.__init__(this, instance)

		iface = this.setInterface('BPIC/BP/Fn/Output')
		iface._enum = Enums.BPFnOutput
		iface._dynamicPort = True # Port is initialized dynamically

		funcMain = this.instance._funcMain
		iface._funcMain = funcMain
		funcMain._proxyOutput = this

	def imported(this, data):
		output = this.iface._funcMain.node._funcInstance.output

		for key, value in output.items():
			this.createPort('input', key, value)

	def update(this, cable):
		iface = this.iface._funcMain
		if(cable == None): # Triggered by port route
			IOutput = iface.output
			Output = iface.node.output
			thisInput = this.input

			# Sync all port value
			for key, value in IOutput.items():
				if(value.type == Types.Function): continue
				Output[key](thisInput[key]())

			return

		iface.node.output[cable.input.name](cable.value())

@registerInterface('BPIC/BP/Fn/Main')
class FnMain(Interface):
	_importOnce = False
	_save = None
	_portSw_ = None
	def _BpFnInit(this):
		if(this._importOnce):
			raise Exception("Can't import function more than once")

		this._importOnce = True
		node = this.node

		# ToDo: will this be slower if we lazy import the module like below?
		from ..Engine import Engine
		this._bpInstance = Engine()

		bpFunction = node._funcInstance

		newInstance = this._bpInstance
		newInstance.variables = [] # _for one function
		newInstance.sharedVariables = bpFunction.variables # shared between function
		newInstance.functions = node.instance.functions
		newInstance._funcMain = this
		newInstance._mainInstance = bpFunction.rootInstance

		bpFunction.refreshPrivateVars(newInstance)

		swallowCopy = bpFunction.structure[0:]
		this._bpInstance.importJSON(swallowCopy)

		# Init port switches
		if(this._portSw_ != None):
			this._initPortSwitches(this._portSw_)
			this._portSw_ = None

			InputIface = this._proxyInput.iface
			if(InputIface._portSw_ != None):
				InputIface._initPortSwitches(InputIface._portSw_)
				InputIface._portSw_ = None

		def _save(ev, eventName, force=False):
			if(force or bpFunction._syncing): return

			# ev.bpFunction = bpFunction
			newInstance._mainInstance.emit(eventName, ev)

			bpFunction._syncing = True
			bpFunction._onFuncChanges(eventName, ev, this.node)
			bpFunction._syncing = False

		this._save = _save
		this._bpInstance.on('cable.connect cable.disconnect node.created node.delete node.id.changed', this._save)

	def renamePort(this, which, fromName, toName):
		this.node._funcInstance.renamePort(which, fromName, toName)
		(this._save)(False, False, True)

class BPFnInOut(Interface):
	def addPort(this, port: PortClass, customName):
		if(port == None): raise Exception("Can't set type with None")

		if(port.iface.namespace.startswith("BP/Fn")):
			raise Exception("Function Input can't be connected directly to Output")

		name = ''
		if(customName != None):
			if(port._name != None):
				name = port._name.name
			else: name = customName
		else: name = port.name

		reff = None
		if(port.feature == Port.Trigger):
			reff = {'node': {}, 'port': {}}
			def callback():
				reff['node'].output[reff['port'].name]()

			portType = Port.Trigger(callback)
		else: portType = port.feature != port._getPortFeature() if None else port.type

		# nodeA, nodeB # Main (input) . Input (output), Output (input) . Main (output)
		if(this.type == 'bp-fn-input'): # Main (input): . Input (output):
			inc = 1
			while(name in this.output):
				if((name + inc) in this.output): inc += 1
				else:
					name += inc
					break

			nodeA = this._funcMain.node
			nodeB = this.node
			nodeA._funcInstance.input[name] = portType

		else: # Output (input) . Main (output)
			inc = 1
			while(name in this.input):
				if((name + inc) in this.input): inc += 1
				else:
					name += inc
					break

			nodeA = this.node
			nodeB = this._funcMain.node
			nodeB._funcInstance.output[name] = portType

		outputPort = nodeB.createPort('output', name, portType)

		if(portType == Types.Function):
			inputPort = nodeA.createPort('input', name, Port.Trigger(outputPort._callAll))
		else: inputPort = nodeA.createPort('input', name, portType)

		if(reff != None):
			reff['node'] = nodeB
			reff['port'] = inputPort

		if(this.type == 'bp-fn-input'):
			outputPort._name = {"name": name} # When renaming port, this also need to be changed
			this.emit("_add.[name]", outputPort)

			def callback(ev):
				outputPort.iface.node.output[outputPort.name](ev.cable.output.value)
			
			inputPort.on('value', callback) 
			return outputPort

		inputPort._name = {"name": name} # When renaming port, this also need to be changed
		this.emit("_add.[name]", inputPort)
		return inputPort

	def renamePort(this, fromName, toName):
		bpFunction = this._funcMain.node._funcInstance

		# Main (input) . Input (output)
		if(this.type == 'bp-fn-input'):
			bpFunction.renamePort('input', fromName, toName)
		
		# Output (input) . Main (output)
		else: bpFunction.renamePort('output', fromName, toName)

	def deletePort(this, name):
		funcMainNode = this._funcMain.node
		if(this.type == 'bp-fn-input'): # Main (input): . Input (output):
			funcMainNode.deletePort('input', name)
			this.node.deletePort('output', name)

			del funcMainNode._funcInstance.input[name]

		else: # Output (input) . Main (output)
			funcMainNode.deletePort('output', name)
			this.node.deletePort('input', name)

			del funcMainNode._funcInstance.output[name]

@registerInterface('BPIC/BP/Fn/Input')
class FnInput(BPFnInOut):
	Output = []
	def __init__(this, node):
		BPFnInOut.__init__(this, node)
		this.title = 'Input'
		this.type = 'bp-fn-input'

@registerInterface('BPIC/BP/Fn/Output')
class FnOutput(BPFnInOut):
	Input = []
	def __init__(this, node):
		BPFnInOut.__init__(this, node)
		this.title = 'Output'
		this.type = 'bp-fn-output'