from . import Internal, Types as PortType, PortGhost, Interface, Utils, Nodes, Environment
from .Interface import Temp
from .Port import PortFeature as Port
from .Constructor import CustomEvent
from typing import Dict, List
import json as JSON

class Engine(CustomEvent):
	iface: Dict[str, Interface] = {}
	ifaceList: List[Interface] = []
	_settings = {}
	disablePorts = False
	throwOnError = True

	variables = {}
	functions = {}
	ref: Dict[str, Interface] = {}

	# @var Nodes/FnMain 
	_funcMain = None

	def deleteNode(this, iface):
		list = this.ifaceList
		i = Utils.findFromList(list, iface)

		if(i != -1):
			list.pop(i)
		else:
			if(this.throwOnError):
				raise Exception("Node to be deleted was not found")

			return this.emit('error', {
				"type": 'node_delete_not_found',
				"data": {"iface": iface}
			})

		# iface._bpDestroy = True

		eventData = {"iface": iface}
		this.emit('node.delete', eventData)

		iface.node.destroy()
		iface.destroy()

		check = Temp.list
		for val in check:
			portList = iface[val]
			for port in portList:
				portList[port].disconnectAll(this._remote != None)

		routes = iface.node.routes
		if(routes.inp.length != 0):
			inp = routes.inp
			for cable in inp:
				cable.disconnect()

		if(routes.out != None): routes.out.disconnect()

		# Delete reference
		del this.iface[iface.id]
		del this.ref[iface.id]

		parent = iface.node._funcInstance
		if(parent != None):
			del parent.rootInstance.ref[iface.id]

		this.emit('node.deleted', eventData)

	def clearNodes(this):
		list = this.ifaceList
		for iface in list:
			if(iface == None): continue

			iface.node.destroy()
			iface.destroy()

		this.ifaceList = []
		this.iface = []
		this.ref = []

	def importJSON(this, json, options={}):
		if(isinstance(json, str)):
			json = JSON.loads(json)

		appendMode = options.has_key('appendMode') & options['appendMode'] == False
		if(not appendMode): this.clearNodes()

		# Do we need this?
		# this.emit("json.importing",:appendMode: options.appendMode, raw: json})

		metadata = json['_']
		del json['_']
		
		if(metadata != None):
			if(metadata.has_key('env')):
				Environment.imports(metadata['env'])

			if(metadata.has_key('functions')):
				functions = metadata['functions']
	
				for key, value in functions.items():
					this.createFunction(key, value)

	
			if(metadata.has_key('variables')):
				variables = metadata['variables']
	
				for key, value in variables.items():
					this.createVariable(key, value)

		inserted = this.ifaceList
		nodes = []
		appendLength = len(inserted) if appendMode else 0

		# Prepare all ifaces based on the namespace
		# before we create cables for them
		for namespace, ifaces in json.items():
			# Every ifaces that using this namespace name
			for iface in ifaces:
				iface['i'] += appendLength
				ifaceOpt = {
					'id': iface['id'] if iface.has_key('id') else None,
					'i': iface['i']
				}

				if(iface.has_key('data')):
					ifaceOpt['data'] = iface['data']
				if(iface.has_key('input_d')):
					ifaceOpt['input_d'] = iface['input_d']
				if(iface.has_key('output_sw')):
					ifaceOpt['output_sw'] = iface['output_sw']

				# @var Interface | Nodes.FnMain 
				temp = this.createNode(namespace, ifaceOpt, nodes)
				inserted[iface['i']] = temp # Don't add  as it's already reference

				# For custom function node
				temp._BpFnInit()

		# Create cable only from output and property
		# > Important to be separated from above, so the cable can reference to loaded ifaces
		for namespace, ifaces in json.items():
			# Every ifaces that using this namespace name
			for ifaceJSON in ifaces:
				iface = inserted[ifaceJSON['i']]

				if(ifaceJSON.has_key('route')):
					iface.node.routes.routeTo(inserted[ifaceJSON['route']['i']])

				# If have output connection
				if(ifaceJSON.has_key('output')):
					out = ifaceJSON['output']

					# Every output port that have connection
					for portName, ports in out.items():
						linkPortA = iface.output[portName]

						if(linkPortA == None):
							if(iface._enum == Nodes.Enums.BPFnInput):
								target = this._getTargetPortType(iface.node.instance, 'input', ports)
								linkPortA = iface.addPort(target, portName)

								if(linkPortA == None):
									raise Exception("Can't create output port ([portName]) for function ([iface._funcMain.node._funcInstance.id])")

							elif(iface._enum == Nodes.Enums.BPVarGet):
								target = this._getTargetPortType(this, 'input', ports)
								iface.useType(target)
								linkPortA = iface.output[portName]

							else: raise Exception("Node port not found for iface (index: ifaceJSON[i], title: iface.title), with port name: portName")

						# Current output's available targets
						for target in ports:
							target['i'] += appendLength
							targetNode = inserted[target['i']]

							# output can only meet input port
							linkPortB = targetNode.input[target['name']]
							if(linkPortB == None):
								if(targetNode._enum == Nodes.Enums.BPFnOutput):
									linkPortB = targetNode.addPort(linkPortA, target['name'])

									if(linkPortB == None):
										raise Exception("Can't create output port ([target['name']]) for function ([targetNode._funcMain.node._funcInstance.id])")

								elif(targetNode._enum == Nodes.Enums.BPVarSet):
									targetNode.useType(linkPortA)
									linkPortB = targetNode.input[target['name']]

								elif(linkPortA.type == PortType.Route):
									linkPortB = targetNode.node.routes

								else: raise Exception("Node port not found for targetNode.title with name: target[name]")

							# echo "\n[current.title].[linkPortA.name]: [targetNode.title].[linkPortB.name]"

							linkPortA.connectPort(linkPortB)
							# cable._print()

		# Call nodes init after creation processes was finished
		for val in nodes:
			val.init()

		return inserted

	def settings(this, which, val):
		if(val == None):
			return this.settings[which]

		this.settings[which] = val

	def _getTargetPortType(this, instance, whichPort, targetNodes):
		target = targetNodes[0] # ToDo: check all target in case if it's supporting Union type
		targetIface = instance.ifaceList[target['i']]
		return targetIface[whichPort][target['name']]

	def getNode(this, id):
		ifaces = this.ifaceList

		for val in ifaces:
			if(val.id == id or val.i == id):
				return val.node

	def getNodes(this, namespace):
		ifaces = this.ifaceList
		got = []

		for val in ifaces:
			if(val.namespace == namespace):
				got.append(val.node)

		return got

	# ToDo: sync with JS, when creating function node this still broken
	def createNode(this, namespace, options=None, nodes=None):
		func = Utils.deepProperty(Internal.nodes, namespace.split('/'))

		# Try to load from registered namespace folder if exist
		funcNode = None
		if(func == None):
			if(namespace.startswith("BPI/F/")):
				func = Utils.deepProperty(this.functions, namespace[6:].split('/'))

				if(func != None):
					funcNode = (func.node)(this)

			else:
				Internal._loadNamespace(namespace)
				func = Utils.deepProperty(Internal.nodes, namespace.split('/'))

			if(func == None):
				raise Exception("Node nodes for namespace was not found, maybe .registerNode() haven't being called?")

		# @var Node 
		node = funcNode if funcNode != None else func(this)
		iface = node.iface

		# Disable data flow on any node ports
		if(this.disablePorts): node.disablePorts = True

		if(iface == None):
			raise Exception("Node interface was not found, do you forget to call \$node.setInterface() ?")

		# Create the linker between the nodes and the iface
		if(funcNode == None):
			iface._prepare_(func)

		iface.namespace = namespace
		if(options.has_key('id')):
			iface.id = options['id']
			this.iface[iface.id] = iface
			this.ref[iface.id] = iface.ref

			parent = iface.node._funcInstance
			if(parent != None):
				parent.rootInstance.ref[iface.id] = iface.ref

		if(options.has_key('i')):
			iface.i = options['i']
			this.ifaceList[iface.i] = iface

		else: this.ifaceList.append(iface)

		defaultInputData = options['input_d']
		if(defaultInputData != None):
			iface._importInputs(defaultInputData)

		savedData = options['data']
		portSwitches = options['output_sw']

		if(portSwitches != None):
			for key, val in portSwitches.items():
				ref = iface.output[key]

				if((val | 1) == 1):
					Port.StructOf_split(ref)

				if((val | 2) == 2):
					ref.allowResync = True

		iface.importing = False

		iface.imported(savedData)
		node.imported(savedData)

		if(nodes != None):
			nodes.append(node)

		iface.init()

		if(nodes == None):
			node.init()

		return iface

	def createVariable(this, id, options):
		if(this.variables.has_key(id)):
			this.variables[id].destroy()
			del this.variables[id]

		# deepProperty

		# BPVariable = ./nodes/Var.js
		temp = Nodes.BPVariable(id, options)
		this.variables[id] = temp
		this.emit('variable.new', temp)

		return temp

	def createFunction(this, id, options):
		if(this.functions.has_key(id)):
			this.functions[id].destroy()
			del this.functions[id]

		# BPFunction = ./nodes/Fn.js
		temp = Nodes.BPFunction(id, options, this)
		this.functions[id] = temp

		if(options.has_key('vars')):
			vars = options['vars']
			for val in vars:
				temp.createVariable(val, {"scope": Nodes.VarScope.shared})

		if(options.has_key('privateVars')):
			privateVars = options['privateVars']
			for val in privateVars:
				temp.addPrivateVars(val)

		this.emit('function.new', temp)
		return temp

	def _log(this, data):
		data.instance = this

		if(this._mainInstance != None):
			this._mainInstance.emit('log', data)
		else: this.emit('log', data)

	def destroy(this):
		this.clearNodes()

def deepMerge(real, opt):
	for key, val in opt.items():
		if(isinstance(val, list)):
			deepMerge(real[key], val)
			continue

		real[key] = val