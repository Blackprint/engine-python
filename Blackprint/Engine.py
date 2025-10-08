import re
import asyncio
from .Nodes.Enums import Enums
from .Nodes.BPFunction import FnMain, BPFunction
from .Nodes.BPVariable import VarScope, BPVariable
from .Types import Types
from .Environment import Environment
from .Utils import Utils
from .Internal import EvError, EvIface, Internal, EvVariableNew, EvVariableRenamed, EvVariableDeleted, EvFunctionNew, EvFunctionRenamed, EvFunctionDeleted, EvNodeIdChanged, EvNodeCreating, EvNodeCreated, EvJsonImporting, EvJsonImported
from .Interface import Temp, Interface
from .Port.PortFeature import Port
from .Constructor.CustomEvent import CustomEvent
from .Constructor.ExecutionOrder import ExecutionOrder
from .Constructor.Cable import Cable
from .Constructor.InstanceEvent import InstanceEvents
from typing import Dict, List
from .Event import Event
import json as JSON

class Engine(CustomEvent):
	def __init__(this):
		CustomEvent.__init__(this)

		this.iface: Dict[str, Interface] = {} # { id => IFace }
		this.ifaceList: List[Interface] = []
		this.disablePorts = False # true = disable port data sync and disable route
		this.throwOnError = True
		this._settings = {}

		# Private or function node's instance only
		this.sharedVariables = None

		this.variables = {} # { category => BPVariable{ name, value, type }, category => { category } }
		this.functions = {} # { category => BPFunction{ name, variables, input, output, used: [], node, description }, category => { category } }
		this.ref = {} # { id => Port references }

		this.rootInstance = None
		this._importing = False
		this._destroying = False
		this._ready = False
		this._remote = None
		this._locked_ = False
		this._eventsInsNew = False
		this._destroyed_ = False
		this.parentInterface: FnMain = None

		this.executionOrder = ExecutionOrder(this)
		this.events = InstanceEvents(this)

		this._envDeleted = lambda data: this._envDeletedHandler(data)
		Event.on('environment.deleted', this._envDeleted)

		this.once('json.imported', lambda data: this._onJsonImported())

		# For remote control
		this.syncDataOut = True

	def deleteNode(this, iface):
		list = this.ifaceList
		i = Utils.findFromList(list, iface)

		if(i != None):
			iface._bpDestroy = True
			eventData = EvIface(iface)
			this._emit('node.delete', eventData)
			list.pop(i)
		else:
			if(this.throwOnError):
				raise Exception("Node to be deleted was not found")

			return this._emit('error', EvError('node_delete_not_found', EvIface(iface)))

		iface.node.destroy()
		iface.destroy()

		check = Temp.list
		for val in check:
			if(not hasattr(iface, val)): continue

			portList = getattr(iface, val)
			if(portList == None): continue

			for port in portList:
				portList[port].disconnectAll(this._remote != None)

		routes = iface.node.routes
		if(len(routes.inp) != 0):
			inp = routes.inp
			for cable in inp:
				cable.disconnect()

		if(routes.out != None): routes.out.disconnect()

		# Delete reference
		if(iface.id != None and iface.id != ""):
			del this.iface[iface.id]
			del this.ref[iface.id]

			parent = iface.node.bpFunction
			if(parent != None):
				del parent.rootInstance.ref[iface.id]

		this._emit('node.deleted', eventData)

	def clearNodes(this):
		if(this._locked_): raise Exception("This instance was locked")
		this._destroying = True

		list = this.ifaceList
		for iface in list:
			if(iface == None): continue

			eventData = EvIface(iface)
			this._emit('node.delete', eventData)

			iface.node.destroy()
			iface.destroy()

			this._emit('node.deleted', eventData)

		this.ifaceList = []
		this.iface = {}
		this.ref = {}

		this._destroying = False

	def importJSON(this, json, options: Dict={}):
		if(isinstance(json, str)):
			json = JSON.loads(json)

		# Throw if no instance data in the JSON
		if(not('instance' in json)):
			raise Exception("Instance was not found in the JSON data")

		if(not('appendMode' in options)): options['appendMode'] = False
		if(not('clean' in options)): options['clean'] = True
		if(not('noEnv' in options)): options['noEnv'] = False

		appendMode = options['appendMode']
		if(not appendMode): this.clearNodes()
		reorderInputPort = []

		this._importing = True

		if(options['clean'] != False and not(options['appendMode'])):
			this.clearNodes()
			this.functions = {}
			this.variables = {}
			this.events.list = {}
		elif(not options['appendMode']): this.clearNodes()

		this.emit("json.importing", EvJsonImporting(options['appendMode'], json))

		if('environments' in json and not(options['noEnv'])):
			Environment.imports(json['environments'])

		if('functions' in json):
			functions = json['functions']

			for key, value in functions.items():
				this.createFunction(key, value)

		if('variables' in json):
			variables = json['variables']

			for key, value in variables.items():
				this.createVariable(key, value)

		if('events' in json):
			events = json['events']

			for path, value in events.items():
				this.events.createEvent(path, value)

		inserted = this.ifaceList
		nodes = []
		appendLength = len(inserted) if appendMode else 0
		instance = json['instance']

		# Prepare all ifaces based on the namespace
		# before we create cables for them
		for namespace, ifaces in instance.items():
			# Every ifaces that using this namespace name
			for conf in ifaces:
				conf['i'] += appendLength
				confOpt = { 'i': conf['i'] }

				if('data' in conf):
					confOpt['data'] = conf['data']
				if('id' in conf):
					confOpt['id'] = conf['id']
				if('input_d' in conf):
					confOpt['input_d'] = conf['input_d']
				if('output_sw' in conf):
					confOpt['output_sw'] = conf['output_sw']

				# @var Interface | Nodes.FnMain
				iface = this.createNode(namespace, confOpt, nodes)
				inserted[conf['i']] = iface # Don't add  as it's already reference

				if('input' in conf):
					reorderInputPort.append({
						"iface": iface,
						"config": conf,
					})

				# For custom function node
				iface._BpFnInit()

		# Create cable only from output and property
		# > Important to be separated from above, so the cable can reference to loaded ifaces
		for namespace, ifaces in instance.items():
			# Every ifaces that using this namespace name
			for ifaceJSON in ifaces:
				iface = inserted[ifaceJSON['i']]

				if('route' in ifaceJSON):
					iface.node.routes.routeTo(inserted[ifaceJSON['route']['i'] + appendLength])

				# If have output connection
				if('output' in ifaceJSON):
					out = ifaceJSON['output']

					# Every output port that have connection
					for portName, ports in out.items():
						linkPortA = iface.output.get(portName)

						if(linkPortA == None):
							if(iface._enum == Enums.BPFnInput):
								target = this._getTargetPortType(iface.node.instance, 'input', ports)
								linkPortA = iface.addPort(target, portName)

								if(linkPortA == None):
									raise Exception(f"Can't create output port ({portName}) for function ({iface.parentInterface.node.bpFunction.id})")

							elif(iface._enum == Enums.BPVarGet):
								target = this._getTargetPortType(this, 'input', ports)
								iface.useType(target)
								linkPortA = iface.output[portName]

							else: raise Exception(f"Node port not found for iface (index: {ifaceJSON['i']}, title: {iface.title}), with port name: {portName}")

						# Current output's available targets
						for target in ports:
							target['i'] += appendLength

							# @var \Blackprint\Interfaces|\Blackprint\Nodes\BPFnInOut|\Blackprint\Nodes\BPVarGetSet
							targetNode = inserted[target['i']] # iface

							if(linkPortA.isRoute):
								cable = Cable(linkPortA, None)
								cable.isRoute = True
								cable.output = linkPortA
								linkPortA.cables.append(cable)

								targetNode.node.routes.connectCable(cable)
								continue

							# output can only meet input port
							linkPortB = targetNode.input.get(target['name'])
							if(linkPortB == None):
								if(targetNode._enum == Enums.BPFnOutput):
									linkPortB = targetNode.addPort(linkPortA, target['name'])

									if(linkPortB == None):
										raise Exception(f"Can't create output port ({target['name']}) for function ({targetNode.parentInterface.node.bpFunction.id})")

								elif(targetNode._enum == Enums.BPVarSet):
									targetNode.useType(linkPortA)
									linkPortB = targetNode.input[target['name']]

								elif(linkPortA.type == Types.Route):
									linkPortB = targetNode.node.routes

								else: raise Exception(f"Node port not found for targetNode.title with name: {target['name']}")

							linkPortA.connectPort(linkPortB)

							# print(f"\n{iface.title}.{linkPortA.name} . {targetNode.title}.{linkPortB.name}")
							# if linkPortA.connectPort(linkPortB):
							# 	print(f"\n{iface.title}.{linkPortA.name} <. {targetNode.title}.{linkPortB.name}")

		# Fix input port cable order
		for value in reorderInputPort:
			iface = value['iface']
			cInput = value['config']['input']

			for key, conf in cInput.items():
				port = iface.input[key]
				cables = port.cables
				temp = len(conf)*[None]

				a = 0
				for ref in conf:
					name = ref['name']
					targetIface = inserted[ref['i'] + appendLength]

					for cable in cables:
						if(cable.output.name != name or cable.output.iface != targetIface): continue

						temp[a] = cable
						break

					a += 1

				for ref in temp:
					if(ref == None): print(f"Some cable failed to be ordered for ({iface.title}: {key})")

				port.cables = temp

		# Call nodes init after creation processes was finished
		for val in nodes:
			val.init()

		this._importing = False
		this.emit("json.imported", EvJsonImported(options['appendMode'], appendLength, inserted, json))
		Utils.runAsync(this.executionOrder.start())

		return inserted

	def settings(this, which, val):
		if(val == None):
			return this._settings[which]

		which = which.replace('.', '_')
		this._settings[which] = val

	def linkVariables(this, vars):
		bpFunction = this.parentInterface.node.bpFunction if this.parentInterface != None else None
		for temp in vars:
			Utils.setDeepProperty(this.variables, temp.id.split('/'), temp)
			this._emit('variable.new', EvVariableNew(temp._scope, temp.id, bpFunction, temp))

	def _getTargetPortType(this, instance, whichPort, targetNodes):
		target = targetNodes[0] # ToDo: check all target in case if it's supporting Union type
		targetIface = instance.ifaceList[target['i']]

		if(whichPort == 'input'):
			return targetIface.input[target['name']]
		else: return targetIface.output[target['name']]

	def getNodes(this, namespace):
		ifaces = this.ifaceList
		got = []

		for val in ifaces:
			if(val.namespace == namespace):
				got.append(val.node)

		return got

	def createVariable(this, id, options):
		if(this._locked_): raise Exception("This instance was locked")
		if(re.search(r'/\s/', id) != None):
			raise Exception(f"Id can't have space character: '{id}'")

		ids = id.split('/')
		lastId = ids[len(ids) - 1]
		parentObj = Utils.getDeepProperty(this.variables, ids, 1)

		if(parentObj != None and lastId in parentObj):
			if(parentObj[lastId].isShared): return

			this.variables[id].destroy()
			del this.variables[id]

		# setDeepProperty

		# BPVariable = ./nodes/Var.js
		temp = BPVariable(id, options)
		Utils.setDeepProperty(this.variables, ids, temp)

		bpFunction = this.parentInterface.node.bpFunction if this.parentInterface != None else None
		temp._scope = VarScope.Public
		this._emit('variable.new', EvVariableNew(temp._scope, temp.id, bpFunction, temp))

		return temp

	def renameVariable(this, from_, to, scopeId):
		from_ = re.sub(r'^/|/$', '', from_)
		from_ = re.sub(r'[`~!@#$%^&*()\-_+={}\[\]:"|;\'\\,<>\?]+', '_', from_)
		to = re.sub(r'^/|/$', '', to)
		to = re.sub(r'[`~!@#$%^&*()\-_+={}\[\]:"|;\'\\,<>\?]+', '_', to)

		instance, varsObject = None, None
		if(scopeId == VarScope.Public):
			instance = this.rootInstance if this.rootInstance != None else this
			varsObject = instance.variables
		elif(scopeId == VarScope.Private):
			instance = this
			if(instance.rootInstance == None):
				raise Exception("Can't rename private function variable from main instance")
			varsObject = instance.variables
		elif(scopeId == VarScope.Shared):
			return # Already handled on nodes/Fn.py

		# Old variable object
		ids = from_.split('/')
		oldObj = Utils.getDeepProperty(varsObject, ids)
		if(oldObj == None):
			raise Exception(f"Variable with name '{from_}' was not found")

		# New target variable object
		ids2 = to.split('/')
		if(Utils.getDeepProperty(varsObject, ids2) != None):
			raise Exception(f"Variable with similar name already exist in '{to}'")

		map = oldObj.used
		for iface in map:
			iface.title = iface.data.name = to

		oldObj.id = oldObj.title = to

		Utils.deleteDeepProperty(varsObject, ids, True)
		Utils.setDeepProperty(varsObject, ids2, oldObj)

		bpFunction = this.parentInterface.node.bpFunction if this.parentInterface != None else None
		if(scopeId == VarScope.Private):
			instance._emit('variable.renamed', EvVariableRenamed(scopeId, from_, to, bpFunction, None))
		else:
			instance._emit('variable.renamed', EvVariableRenamed(scopeId, from_, to, bpFunction, oldObj))

	def deleteVariable(this, namespace, scopeId):
		varsObject, instance = None, this
		if(scopeId == VarScope.Public):
			instance = this.rootInstance if this.rootInstance != None else this
			varsObject = instance.variables
		elif(scopeId == VarScope.Private):
			varsObject = instance.variables
		elif(scopeId == VarScope.Shared):
			varsObject = instance.sharedVariables

		path = namespace.split('/')
		oldObj = Utils.getDeepProperty(varsObject, path)
		if(oldObj == None): return
		oldObj.destroy()

		bpFunction = this.parentInterface.node.bpFunction if this.parentInterface != None else None

		Utils.deleteDeepProperty(varsObject, path, True)
		this._emit('variable.deleted', EvVariableDeleted(scopeId, oldObj.id, bpFunction))

	def createFunction(this, id, options):
		if(this._locked_): raise Exception("This instance was locked")
		if(re.search(r'/\s/', id) != None):
			raise Exception(f"Id can't have space character: '{id}'")

		ids = id.split('/')
		lastId = ids[len(ids) - 1]
		parentObj = Utils.getDeepProperty(this.functions, ids, 1)

		if(parentObj != None and lastId in parentObj):
			parentObj[lastId].destroy()
			del parentObj[lastId]

		# BPFunction = ./nodes/Fn.js
		temp = BPFunction(id, options, this)
		Utils.setDeepProperty(this.functions, ids, temp)

		if('vars' in options):
			vars = options['vars']
			for val in vars:
				temp.createVariable(val, {"scope": VarScope.Shared})

		if('privateVars' in options):
			privateVars = options['privateVars']
			for val in privateVars:
				temp.createVariable(val, {"scope": VarScope.Private})

		this._emit('function.new', EvFunctionNew(temp))
		return temp

	def renameFunction(this, from_, to):
		from_ = re.sub(r'^/|/$', '', from_)
		from_ = re.sub(r'[`~!@#$%^&*()\-_+={}\[\]:"|;\'\\,<>\?]+', '_', from_)
		to = re.sub(r'^/|/$', '', to)
		to = re.sub(r'[`~!@#$%^&*()\-_+={}\[\]:"|;\'\\,<>\?]+', '_', to)

		# Old function object
		ids = from_.split('/')
		oldObj = Utils.getDeepProperty(this.functions, ids)
		if(oldObj == None):
			raise Exception(f"Function with name '{from_}' was not found")

		# New target function object
		ids2 = to.split('/')
		if(Utils.getDeepProperty(this.functions, ids2) != None):
			raise Exception(f"Function with similar name already exist in '{to}'")

		map = oldObj.used
		for iface in map:
			iface.namespace = 'BPI/F/'+to
			if(iface.title == from_): iface.title = to

		if(oldObj.title == from_): oldObj.title = to
		oldObj.id = to

		Utils.deleteDeepProperty(this.functions, ids, True)
		Utils.setDeepProperty(this.functions, ids2, oldObj)

		this._emit('function.renamed', EvFunctionRenamed(from_, to, oldObj))

	def deleteFunction(this, id):
		path = id.split('/')
		oldObj = Utils.getDeepProperty(this.functions, path)
		if(oldObj == None): return
		oldObj.destroy()

		Utils.deleteDeepProperty(this.functions, path, True)
		this._emit('function.deleted', EvFunctionDeleted(oldObj.id, oldObj))

	def _log(this, data):
		data.instance = this

		if(this.rootInstance != None):
			this.rootInstance._emit('log', data)
		else: this._emit('log', data)

	def _emit(this, evName, data=[]):
		this.emit(evName, data)
		if(this.parentInterface == None): return

		rootInstance = this.parentInterface.node.bpFunction.rootInstance
		if(rootInstance._remote == None): return
		rootInstance.emit(evName, data)

	def _envDeletedHandler(this, key):
		list = this.ifaceList
		for iface in reversed(list):
			if(iface.namespace != 'BP/Env/Get' and iface.namespace != 'BP/Env/Set'): continue
			if(iface.data.name == key): this.deleteNode(iface)

	def _onJsonImported(this):
		this._ready = True
		if(hasattr(this, '_readyResolve') and this._readyResolve != None):
			this._readyResolve()

	def ready(this):
		if(this._ready): return
		if(hasattr(this, '_readyPromise') and this._readyPromise != None):
			return this._readyPromise

		this._readyPromise = asyncio.Future()
		this._readyResolve = lambda: this._readyPromise.set_result(None)
		return this._readyPromise

	def changeNodeId(this, iface, newId):
		if(this._locked_): raise Exception("This instance was locked")

		sketch = iface.node.instance
		oldId = iface.id
		if(oldId == newId or hasattr(iface, 'importing') and iface.importing): return

		if(oldId != None and oldId != ""):
			del sketch.iface[oldId]
			del sketch.ref[oldId]

			if(sketch.parentInterface != None):
				del sketch.parentInterface.ref[oldId]

		newId = newId if newId != None else ''
		iface.id = newId

		if(newId != ''):
			sketch.iface[newId] = iface
			sketch.ref[newId] = iface.ref

			if(sketch.parentInterface != None):
				sketch.parentInterface.ref[newId] = iface.ref

		iface.node.instance.emit('node.id.changed', EvNodeIdChanged(iface, oldId, newId))

	def _isInsideFunction(this, fnNamespace):
		if(this.rootInstance == None): return False
		if(this.parentInterface.namespace == fnNamespace): return True
		return this.parentInterface.node.instance._isInsideFunction(fnNamespace)

	def _tryInitUpdateNode(this, node, rule, creatingNode):
		if((rule & Enums.WhenCreatingNode)):
			if(not creatingNode): return
		elif(creatingNode): return

		# There are no cable connected when creating node
		# So.. let's skip these checks
		if(not creatingNode):
			if((rule & Enums.NoRouteIn) and len(node.routes.inp) != 0): return
			if((rule & Enums.NoInputCable)):
				input = node.iface.input
				for key in input:
					if(len(input[key].cables) != 0): return

		node.update()

	def createNode(this, namespace, options={}, nodes=None):
		if(this._locked_): raise Exception("This instance was locked")

		if(namespace == "BP/Fn/Input" and this.parentInterface != None):
			funcMain = this.parentInterface
			if(funcMain._proxyInput != None):
				# Disallow to have more than one proxy input
				print("Function node can't have more than one proxy input")
				return None

		func = Internal.nodes.get(namespace)

		# Try to load from registered namespace folder if exist
		funcNode = None
		if(namespace.startswith("BPI/F/")):
			func = this.functions.get(namespace[6:])

			if(func != None):
				funcNode = func.node(this)

		if(func == None):
			raise Exception(f"Node nodes for namespace '{namespace}' was not found, maybe .registerNode() haven't being called?")

		this.emit('node.creating', EvNodeCreating(namespace, options))

		# @var Node
		node = funcNode if funcNode != None else func(this)
		iface = node.iface

		# Disable data flow on any node ports
		if(this.disablePorts): node.disablePorts = True

		if(iface == None):
			raise Exception("Node interface was not found, do you forget to call node.setInterface() ?")

		iface.namespace = namespace

		# Create the linker between the nodes and the iface
		if(funcNode == None):
			iface._prepare_(func)

		if('id' in options):
			iface.id = options['id']
			this.iface[iface.id] = iface
			this.ref[iface.id] = iface.ref

			parent = iface.node.bpFunction
			if(parent != None):
				parent.rootInstance.ref[iface.id] = iface.ref

		savedData = options['data'] if 'data' in options else None
		portSwitches = options['output_sw'] if 'output_sw' in options else None

		if('i' in options):
			iface.i = options['i']

			ii = len(this.ifaceList)
			while ii <= iface.i:
				ii += 1
				this.ifaceList.append(None)

			this.ifaceList[iface.i] = iface
		else: this.ifaceList.append(iface)

		node.initPorts(savedData)

		if('input_d' in options):
			defaultInputData = options['input_d']
			if(defaultInputData != None):
				iface._importInputs(defaultInputData)

		if(portSwitches != None):
			for key, val in portSwitches.items():
				ref = iface.output[key]

				if(val & 1):
					Port.StructOf_split(ref)

				if(val & 2):
					ref.allowResync = True

		iface.importing = False

		iface.imported(savedData)
		node.imported(savedData)

		if(nodes != None):
			nodes.append(node)
		else:
			node.init()
			iface.init()

		if(hasattr(func, 'initUpdate') and func.initUpdate != None):
			this._tryInitUpdateNode(node, func.initUpdate, True)

		this.emit('node.created', EvNodeCreated(iface))
		return iface

	def destroy(this):
		this._locked_ = False
		this._destroyed_ = True
		this.clearNodes()

		Event.off('_eventInstance.new', this._eventsInsNew)
		Event.off('environment.deleted', this._envDeleted)
		this.emit('destroy')

def deepMerge(real, opt):
	for key, val in opt.items():
		if(isinstance(val, list)):
			deepMerge(real[key], val)
			continue

		real[key] = val

Internal.interface['BP/default'] = Interface