import re
import asyncio

from typing import Dict

from ..Port.PortFeature import Port
from ..Utils import Utils
from ..Interface import Interface
from ..Node import Node
from ..Constructor.CustomEvent import CustomEvent
from ..Constructor.Port import Port as PortClass
from .BPVariable import VarScope, BPVariable
from ..Types import Types
from .Enums import Enums
from ..Internal import EvVariableNew, EvVariableRenamed, EvVariableDeleted, EvFunctionPortRenamed, EvFunctionPortDeleted, EvPortValue, registerNode, registerInterface
import re

# Don't delete even unused, this is needed for importing the internal node
from .FnPortVar import PortName, FnVarInput, getFnPortType
from .BPEvent import BPEventListen


# used for instance.createFunction
class BPFunction(CustomEvent): # <= bpFunction
	node = None # Node constructor (Function)

	def __init__(this, id, options, instance):
		CustomEvent.__init__(this)

		this.variables: Dict[str, BPVariable] = {} # shared between function
		this.privateVars = [] # private variable (different from other function)

		this._input = {} # Port template
		this._output = {} # Port template
		this.rootInstance = instance # root instance (Blackprint.Engine)

		id = re.sub(r'^/|/$', '', id)
		id = re.sub(r'[`~!@#$%^&*()\-_+={}\[\]:"|;\'\\,.<>?]+', '_', id)
		this.id = id
		this.title = options['title'] if 'title' in options else id
		#this.description = options['description'] if 'description' in options else ''

		input = this._input
		output = this._output
		this.used = [] # [Interface, ...]

		# This will be updated if the function sketch was modified
		if('structure' in options):
			this.structure = options['structure']
		else:
			this.structure = {
				'_bpStale': False,
				'instance': {
					'BP/Fn/Input': [{'i': 0}],
					'BP/Fn/Output': [{'i': 1}],
				},
			}

		# Event listeners for environment, variable, function, and event renaming
		this._envNameListener = lambda ev: this._onEnvironmentRenamed(ev)
		this._varNameListener = lambda ev: this._onVariableRenamed(ev)
		this._funcNameListener = lambda ev: this._onFunctionRenamed(ev)
		this._funcPortNameListener = lambda ev: this._onFunctionPortRenamed(ev)
		this._eventNameListener = lambda ev: this._onEventRenamed(ev)

		# Register event listeners
		this.rootInstance.on('environment.renamed', this._envNameListener)
		this.rootInstance.on('variable.renamed', this._varNameListener)
		this.rootInstance.on('function.renamed', this._funcNameListener)
		this.rootInstance.on('function.port.renamed', this._funcPortNameListener)
		this.rootInstance.on('event.renamed', this._eventNameListener)

		temp = this
		uniqId = 0

		def nodeContruct(instance):
			nonlocal uniqId

			BPFunctionNode.input = input
			BPFunctionNode.output = output
			BPFunctionNode.namespace = id
			BPFunctionNode.type = 'function'

			node = BPFunctionNode(instance)
			iface = node.iface

			instance.bpFunction = temp
			node.bpFunction = temp
			#iface.description = temp.description
			iface.title = temp.title
			iface.type = 'function'
			uniqId += 1
			iface.uniqId = uniqId

			iface._enum = Enums.BPFnMain
			iface._prepare_(BPFunctionNode)
			return node

		this.node = nodeContruct

		# For direct function invocation
		this.directInvokeFn = None
		this._syncing = False

	def _onEnvironmentRenamed(this, ev):
		"""Handle environment name changes"""
		instance = this.structure['instance']
		list_ = []
		if 'BP/Env/Get' in instance:
			list_.extend(instance['BP/Env/Get'])
		if 'BP/Env/Set' in instance:
			list_.extend(instance['BP/Env/Set'])

		for item in list_:
			if item['data']['name'] == ev.old:
				item['data']['name'] = ev.now
				item['data']['title'] = ev.now

	def _onVariableRenamed(this, ev):
		"""Handle variable name changes"""
		instance = this.structure['instance']
		if ev.scope in [VarScope.Public, VarScope.Shared]:
			list_ = []
			if 'BP/Var/Get' in instance:
				list_.extend(instance['BP/Var/Get'])
			if 'BP/Var/Set' in instance:
				list_.extend(instance['BP/Var/Set'])

			for item in list_:
				if item['data']['scope'] == ev.scope and item['data']['name'] == ev.old:
					item['data']['name'] = ev.now

	def _onFunctionRenamed(this, ev):
		"""Handle function name changes"""
		instance = this.structure['instance']
		if f'BPI/F/{ev.old}' not in instance:
			return
		instance[f'BPI/F/{ev.now}'] = instance[f'BPI/F/{ev.old}']
		del instance[f'BPI/F/{ev.old}']

	def _onFunctionPortRenamed(this, ev):
		"""Handle function port name changes"""
		instance = this.structure['instance']
		funcs = instance.get(f'BPI/F/{ev.reference.id}')
		if funcs is None:
			return

		for item in funcs:
			if ev.which == 'output':
				if item.get('output_sw') and ev.old in item['output_sw']:
					item['output_sw'][ev.now] = item['output_sw'][ev.old]
					del item['output_sw'][ev.old]
			elif ev.which == 'input':
				if item.get('input_d') and ev.old in item['input_d']:
					item['input_d'][ev.now] = item['input_d'][ev.old]
					del item['input_d'][ev.old]

	def _onEventRenamed(this, ev):
		"""Handle event name changes"""
		instance = this.structure['instance']
		list_ = []
		if 'BP/Event/Listen' in instance:
			list_.extend(instance['BP/Event/Listen'])
		if 'BP/Event/Emit' in instance:
			list_.extend(instance['BP/Event/Emit'])

		for item in list_:
			if item['data']['namespace'] == ev.old:
				item['data']['namespace'] = ev.now

	def _onFuncChanges(this, eventName, obj, fromNode):
		list = this.used

		for iface_ in list:
			if(iface_.node == fromNode): continue

			nodeInstance = iface_.bpInstance
			nodeInstance.pendingRender = True # Force recalculation for cable position

			if(eventName == 'cable.connect' or eventName == 'cable.disconnect'):
				input = obj.cable.input
				output = obj.cable.output
				ifaceList = fromNode.iface.bpInstance.ifaceList

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
					targetInput = inputIface.input.get(input.name)
					targetOutput = outputIface.output.get(output.name)

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
				index = Utils.findFromList(fromNode.iface.bpInstance.ifaceList, obj.iface)
				if(index == None):
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
		if('/' in id):
			raise Exception("Slash symbol is reserved character and currently can't be used for creating path")

		if options['scope'] == VarScope.Private:
			if id not in this.privateVars:
				this.privateVars.append(id)
				eventData = EvVariableNew(VarScope.Private, id, this, None)
				this.emit('variable.new', eventData)
				this.rootInstance.emit('variable.new', eventData)

			# Add private variable to all function instances
			for iface in this.used:
				vars = iface.bpInstance.variables
				vars[id] = BPVariable(id)
			return

		elif options['scope'] == VarScope.Public:
			raise Exception("Can't create public variable from a function")

		# Shared variable
		if id in this.variables:
			raise Exception(f"Variable id already exist: {id}")

		temp = BPVariable(id, options)
		temp.bpFunction = this
		temp._scope = options['scope']
		this.variables[id] = temp

		eventData = EvVariableNew(temp._scope, temp.id, this, temp)
		this.emit('variable.new', eventData)
		this.rootInstance.emit('variable.new', eventData)
		return temp

	def renameVariable(this, from_, to, scopeId):
		if scopeId is None:
			raise Exception("Third parameter couldn't be null")
		if '/' in to:
			raise Exception("Slash symbol is reserved character and currently can't be used for creating path")

		to = re.sub(r'^/|/$', '', to)
		to = re.sub(r'[`~!@#$%^&*()\-_+={}\[\]:"|;\'\\,.<>?]+', '_', to)

		if scopeId == VarScope.Private:
			privateVars = this.privateVars
			i = privateVars.index(from_)
			if i == -1:
				raise Exception(f"Private variable with name '{from_}' was not found on '{this.id}' function")
			privateVars[i] = to
		elif scopeId == VarScope.Shared:
			varObj = this.variables.get(from_)
			if varObj is None:
				raise Exception(f"Shared variable with name '{from_}' was not found on '{this.id}' function")

			varObj.id = varObj.title = to
			this.variables[to] = varObj
			if from_ in this.variables:
				del this.variables[from_]

			this.rootInstance.emit('variable.renamed', EvVariableRenamed(scopeId, from_, to, this, varObj))
		else:
			raise Exception(f"Can't rename variable from scopeId: {scopeId}")

		# Update references in all function instances
		lastInstance = None
		if scopeId == VarScope.Shared:
			used = this.variables[to].used
			for iface in used:
				iface.title = iface.data.name = to
				lastInstance = iface.node.instance
		else:
			for iface in this.used:
				lastInstance = iface.bpInstance
				lastInstance.renameVariable(from_, to, scopeId)

	def deleteVariable(this, namespace, scopeId):
		if scopeId == VarScope.Public:
			return this.rootInstance.deleteVariable(namespace, scopeId)

		used = this.used
		path = namespace.split('/')

		if scopeId == VarScope.Private:
			privateVars = this.privateVars
			i = privateVars.index(namespace)
			if i == -1:
				return
			privateVars.pop(i)

			used[0].bpInstance.deleteVariable(namespace, scopeId)

			# Delete from all function node instances
			for instance in used[1:]:
				varsObject = instance.variables
				oldObj = Utils.getDeepProperty(varsObject, path)
				if oldObj is None:
					continue
				if scopeId == VarScope.Private:
					oldObj.destroy()
				Utils.deleteDeepProperty(varsObject, path, True)
				eventData = EvVariableDeleted(oldObj._scope, oldObj.id, this)
				instance.emit('variable.deleted', eventData)
		elif scopeId == VarScope.Shared:
			oldObj = Utils.getDeepProperty(this.variables, path)
			used[0].bpInstance.deleteVariable(namespace, scopeId)

			# Delete from all function node instances
			eventData = EvVariableDeleted(oldObj._scope, oldObj.id, this)
			for iface in used[1:]:  # Skip the first element and iterate directly over the rest
				iface.bpInstance.emit('variable.deleted', eventData)

	def renamePort(this, which, fromName, toName):
		main = this[which]
		main[toName] = main[fromName]
		del main[fromName]

		used = this.used
		proxyPort = 'input' if which == 'output' else 'output'

		for iface in used:
			iface.node.renamePort(which, fromName, toName)

			if which == 'output':
				list_ = iface._proxyOutput
				for item in list_:
					item.iface.renamePort(proxyPort, fromName, toName)
			else:  # input
				temp = iface._proxyInput
				if temp.iface and proxyPort in temp.iface and fromName in temp.iface[proxyPort]:
					temp.iface[proxyPort][fromName]._name.name = toName
				temp.renamePort(proxyPort, fromName, toName)

			ifaces = iface.bpInstance.ifaceList
			for proxyVar in ifaces:
				if (which == 'output' and proxyVar.namespace != "BP/FnVar/Output") or \
				   (which == 'input' and proxyVar.namespace != "BP/FnVar/Input"):
					continue

				if proxyVar.data.get('name') == fromName:
					proxyVar.data['name'] = toName

				if which == 'output' and proxyVar.input and 'Val' in proxyVar.input:
					proxyVar.input['Val']._name.name = toName

		this.rootInstance.emit('function.port.renamed', EvFunctionPortRenamed(fromName, toName, this, which))

	def deletePort(this, which, portName):
		used = this.used
		if len(used) == 0:
			raise Exception("One function node need to be placed to the instance before deleting port")

		main = this[which]
		del main[portName]

		hasDeletion = False
		for iface in used:
			if which == 'output':
				list_ = iface._proxyOutput
				for item in list_:
					item.iface.deletePort(portName)
				hasDeletion = True
			elif which == 'input':
				iface._proxyInput.iface.deletePort(portName)
				hasDeletion = True

		if hasDeletion:
			used[0]._save(False, False, True)
			this.rootInstance.emit('function.port.deleted', EvFunctionPortDeleted(which, portName, this))

	async def invoke(this, input):
		iface = this.directInvokeFn
		if iface is None:
			iface = this.directInvokeFn = this.createNode(this.rootInstance)
			iface.bpInstance.executionOrder.stop = True  # Disable execution order and force to use route cable
			iface.bpInstance.pendingRender = True
			iface.isDirectInvoke = True  # Mark this node as direct invoke, for some optimization

			# For sketch instance, we will remove it from sketch visibility
			sketchScope = iface.node.instance.scope
			if sketchScope is not None:
				list_ = sketchScope('nodes').list
				if iface in list_:
					list_.remove(iface)

			# Wait until ready - using event listener instead of Promise
			ready_event = asyncio.Event()

			def on_ready():
				iface.off('ready', on_ready)
				ready_event.set()

			iface.once('ready', on_ready)
			await ready_event.wait()

		proxyInput = iface._proxyInput
		if proxyInput.routes.out is None:
			raise Exception(f"{this.id}: Blackprint function node must have route port that connected from input node to the output node")

		inputPorts = proxyInput.iface.output
		for key, port in inputPorts.items():
			val = input[key]

			if port.value == val:
				continue  # Skip if value is the same

			# Set the value if different, and reset cache and emit value event after this line
			port.value = val

			# Check all connected cables, if any node need to synchronize
			cables = port.cables
			for cable in cables:
				if cable.hasBranch:
					continue
				inp = cable.input
				if inp is None:
					continue

				inp._cache = None
				inp.emit('value', EvPortValue(inp, iface, cable))

		await proxyInput.routes.routeOut()

		ret = {}
		outputs = iface.node.output
		for key, value in outputs.items():
			ret[key] = value

		return ret

	@property
	def input(this):
		return this._input

	@property
	def output(this):
		return this._output

	@input.setter
	def input(this, v):
		raise Exception("Can't modify port by assigning .input property")

	@output.setter
	def output(this, v):
		raise Exception("Can't modify port by assigning .output property")

	def addPrivateVars(this, id):
		if('/' in id):
			raise Exception("Slash symbol is reserved character and currently can't be used for creating path")

		if(id not in this.privateVars):
			this.privateVars.append(id)

			temp = EvVariableNew(VarScope.Private, id, this, None)
			this.emit('variable.new', temp)
			this.rootInstance.emit('variable.new', temp)

		else: return

		list = this.used
		for iface in list:
			vars = iface.bpInstance.variables
			vars[id] = BPVariable(id)

	def refreshPrivateVars(this, instance):
		vars = instance.variables

		list = this.privateVars
		for id in list:
			vars[id] = BPVariable(id)


	def destroy(this):
		map = this.used
		for iface in map:
			iface.node.instance.deleteNode(iface)

# Main function node
class BPFunctionNode(Node): # Main function node: BPI/F/{FunctionName}
	input = None
	output = None
	namespace = None
	bpFunction = None

	type = 'function'
	def __init__(this, instance):
		Node.__init__(this, instance)
		this.partialUpdate = True
		iface = this.setInterface("BPIC/BP/Fn/Main")
		iface.type = 'function'
		iface._enum = Enums.BPFnMain

	# @var FnMain
	iface = None

	def init(this):
		# This is required when the node is created at runtime (maybe from remote or Sketch)
		if(not this.iface._importOnce): this.iface._BpFnInit()

	def imported(this, data):
		instance = this.bpFunction
		instance.used.append(this.iface)

	def update(this, cable):
		iface = this.iface._proxyInput.iface
		Output = iface.node.output

		if(cable == None): # Triggered by port route
			IOutput = iface.output
			thisInput = this.input

			# Sync all port value
			for key, value in IOutput.items():
				if(value.type == Types.Trigger): continue
				Output[key] = thisInput[key]

			return

		# Update output value on the input node inside the function node
		Output[cable.input.name] = cable.value

	def destroy(this):
		used = this.bpFunction.used

		i = Utils.findFromList(used, this.iface)
		if(i != None): used.pop(i)

		this.iface.bpInstance.destroy()

@registerNode('BP/Fn/Input')
class NodeInput(Node):
	output = {}
	def __init__(this, instance):
		Node.__init__(this, instance)

		iface = this.setInterface('BPIC/BP/Fn/Input')
		iface._enum = Enums.BPFnInput
		iface._proxyInput = True # Port is initialized dynamically

		funcMain = this.instance.parentInterface
		iface.parentInterface = funcMain
		funcMain._proxyInput = this

	def imported(this, data):
		input = this.iface.parentInterface.node.bpFunction.input

		for key, value in input.items():
			this.createPort('output', key, value)

	def request(this, cable):
		name = cable.output.name

		# This will trigger the port to request from outside and assign to this node's port
		this.output[name] = this.iface.parentInterface.node.input[name]

@registerNode('BP/Fn/Output')
class NodeOutput(Node):
	input = {}
	def __init__(this, instance):
		Node.__init__(this, instance)
		this.partialUpdate = True # Trigger this.update(cable) function everytime this node connected to any port that have update

		iface = this.setInterface('BPIC/BP/Fn/Output')
		iface._enum = Enums.BPFnOutput
		iface._dynamicPort = True # Port is initialized dynamically

		funcMain = this.instance.parentInterface
		iface.parentInterface = funcMain
		if not hasattr(funcMain, '_proxyOutput'):
			funcMain._proxyOutput = []
		funcMain._proxyOutput.append(this)

	def imported(this, data):
		output = this.iface.parentInterface.node.bpFunction.output

		for key, value in output.items():
			this.createPort('input', key, value)

	def update(this, cable):
		iface = this.iface.parentInterface
		Output = iface.node.output

		if(cable == None): # Triggered by port route
			IOutput = iface.output
			thisInput = this.input

			# Sync all port value
			for key, value in IOutput.items():
				if(value.type == Types.Trigger): continue
				Output[key] = thisInput[key]

			return

		Output[cable.input.name] = cable.value

@registerInterface('BPIC/BP/Fn/Main')
class FnMain(Interface):
	_importOnce = False
	_save = None
	_portSw_ = None
	_proxyInput = None
	uniqId = None
	# input = {} # Port template
	# output = {} # Port template

	# We won't internally mark this node for having dynamic port
	# The port was defined after the node is imported, the outer port
	# will already have a type

	def _BpFnInit(this):
		if(this._importOnce):
			raise Exception("Can't import function more than once")

		this._importOnce = True
		node = this.node

		# ToDo: will this be slower if we lazy import the module like below?
		from ..Engine import Engine
		this.bpInstance = Engine()
		if(this.data != None and ('pause' in this.data)):
			this.bpInstance.executionOrder.pause = True

		bpFunction = node.bpFunction

		newInstance = this.bpInstance
		newInstance.variables = {} # _for one function
		newInstance.sharedVariables = bpFunction.variables # shared between function
		newInstance.functions = node.instance.functions
		newInstance.events = node.instance.events
		newInstance.parentInterface = this
		newInstance.rootInstance = bpFunction.rootInstance

		bpFunction.refreshPrivateVars(newInstance)

		if bpFunction.structure.get('_bpStale'):
			print(node.iface.namespace + ": Function structure was stale, this maybe get modified or not re-synced with remote sketch on runtime")
			raise Exception("Unable to create stale function structure")

		swallowCopy = bpFunction.structure.copy()
		newInstance.importJSON(swallowCopy, {'clean': False})

		# Init port switches
		if(this._portSw_ != None):
			this._initPortSwitches(this._portSw_)
			this._portSw_ = None

			InputIface = this._proxyInput.iface
			if(InputIface._portSw_ != None):
				InputIface._initPortSwitches(InputIface._portSw_)
				InputIface._portSw_ = None

		def _save(ev, eventName=False, force=False):
			eventName = newInstance._currentEventName

			# this.bpInstance._emit('_fn.structure.update', { 'iface': this });
			if(force or bpFunction._syncing): return
			if(this._bpDestroy): return # Don't synchronize if this function node is deleted

			# This will be synced by remote sketch as this engine dont have exportJSON
			bpFunction.structure['_bpStale'] = True
			# bpFunction.structure = this.bpInstance.exportJSON({
			# 	toRawObject: true,
			# 	exportFunctions: false,
			# 	exportVariables: false,
			# 	exportEvents: false,
			# });

			# ev.bpFunction = bpFunction
			newInstance.rootInstance.emit(eventName, ev)

			bpFunction._syncing = True
			try:
				bpFunction._onFuncChanges(eventName, ev, this.node)
			finally:
				bpFunction._syncing = False

		this._save = _save
		this.bpInstance.on('cable.connect cable.disconnect node.created node.delete node.id.changed port.default.changed _port.split _port.unsplit _port.resync.allow _port.resync.disallow', this._save)

	def imported(this, data): this.data = data
	def renamePort(this, which, fromName, toName):
		this.node.bpFunction.renamePort(which, fromName, toName)
		this._save(False, False, True)

		# this.node.instance._emit('_fn.rename.port', {
		# 	iface: this,
		# 	which,
		# 	fromName,
		# 	toName,
		# })

class BPFnInOut(Interface):
	# @var \Blackprint\Nodes\NodeOutput|\Blackprint\Nodes\NodeInput
	_dynamicPort = True # Port is initialized dynamically
	def addPort(this, port: PortClass, customName):
		if(port == None): return

		if(port.iface.namespace.startswith("BP/Fn")):
			raise Exception("Function Input can't be connected directly to Output")

		name = ''
		if(customName != None):
			if(port._name != None):
				name = port._name.name
			else: name = customName
		else: name = port.name

		# nodeA, nodeB # Main (input) . Input (output), Output (input) . Main (output)
		if(this.type == 'bp-fn-input'): # Main (input) . Input (output):
			inc = 1
			while(name in this.output):
				if((name + str(inc)) in this.output): inc += 1
				else:
					name += str(inc)
					break

			nodeA = this.parentInterface.node
			nodeB = this.node
			refName = PortName(name)

			portType = getFnPortType(port, 'input', this, refName)
			if(portType == Types.Trigger):
				inputPortType = Port.Trigger(lambda _port: _port.iface._proxyInput.output[refName.name]())
			else: inputPortType = portType
			nodeA.bpFunction.input[name] = inputPortType

		else: # Output (input) . Main (output)
			inc = 1
			while(name in this.input):
				if((name + str(inc)) in this.input): inc += 1
				else:
					name += str(inc)
					break

			nodeA = this.node
			nodeB = this.parentInterface.node
			refName = PortName(name)

			portType = getFnPortType(port, 'output', this, refName)
			if(port.type == Types.Trigger):
				inputPortType = Port.Trigger(lambda _port: _port.iface.parentInterface.node.output[refName.name]())
			else: inputPortType = portType
			nodeB.bpFunction.output[name] = inputPortType

		outputPort = nodeB.createPort('output', name, portType)
		inputPort = nodeA.createPort('input', name, inputPortType)

		if(this.type == 'bp-fn-input'):
			outputPort._name = refName # When renaming port, this also need to be changed
			this.emit(f"_add.{name}", outputPort)
			return outputPort

		inputPort._name = refName # When renaming port, this also need to be changed
		this.emit(f"_add.{name}", inputPort)

		# Code below is used when we dynamically modify function output node inside the function node
		# where in a single function we can have multiple output node "BP/Fn/Output"
		list_ = this.parentInterface._proxyOutput
		for item in list_:
			port = item.createPort('input', name, inputPortType)
			port._name = inputPort._name
			this.emit("_add." + name, port)

		return inputPort


	def renamePort(this, fromName, toName):
		bpFunction = this.parentInterface.node.bpFunction

		# Main (input) . Input (output)
		if(this.type == 'bp-fn-input'):
			bpFunction.renamePort('input', fromName, toName)

		# Output (input) . Main (output)
		else: bpFunction.renamePort('output', fromName, toName)

		# this.node.instance._emit('_fn.rename.port', {
		# 	iface: this,
		# 	which, fromName, toName,
		# })

	def deletePort(this, name):
		funcMainNode = this.parentInterface.node
		if(this.type == 'bp-fn-input'): # Main (input): . Input (output):
			funcMainNode.deletePort('input', name)
			this.node.deletePort('output', name)

			del funcMainNode.bpFunction.input[name]

		else: # Output (input) . Main (output)
			funcMainNode.deletePort('output', name)
			this.node.deletePort('input', name)

			del funcMainNode.bpFunction.output[name]

@registerInterface('BPIC/BP/Fn/Input')
class FnInput(BPFnInOut):
	output = {}
	def __init__(this, node):
		BPFnInOut.__init__(this, node)
		this.title = 'Input'
		this.type = 'bp-fn-input'

@registerInterface('BPIC/BP/Fn/Output')
class FnOutput(BPFnInOut):
	input = {}
	def __init__(this, node):
		BPFnInOut.__init__(this, node)
		this.title = 'Output'
		this.type = 'bp-fn-output'