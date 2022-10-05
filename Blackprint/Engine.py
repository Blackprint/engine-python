import asyncio
from .Nodes.Enums import Enums
from .Nodes.BPFunction import FnMain, BPFunction
from .Nodes.BPVariable import VarScope, BPVariable
from .Types import Types as PortType
from .Environment import Environment
from .Utils import Utils
from .Internal import EvError, EvIface, Internal
from .Interface import Temp, Interface
from .Port.PortFeature import Port
from .Constructor.CustomEvent import CustomEvent
from .Constructor.OrderedExecution import OrderedExecution
from typing import Dict, List
import json as JSON

class Engine(CustomEvent):
	def __init__(this):
		CustomEvent.__init__(this)

		this.iface: Dict[str, Interface] = {}
		this.ifaceList: List[Interface] = []
		this.disablePorts = False
		this.throwOnError = True

		this.variables = {}
		this.functions = {}
		this.ref: Dict[str, Interface] = {}

		this._funcMain: FnMain = None
		this._settings = {}
		this.executionOrder = OrderedExecution()

		this._importing = False

	def deleteNode(this, iface):
		list = this.ifaceList
		i = Utils.findFromList(list, iface)

		if(i != -1):
			list.pop(i)
		else:
			if(this.throwOnError):
				raise Exception("Node to be deleted was not found")

			return this.emit('error', EvError('node_delete_not_found', EvIface(iface)))

		# iface._bpDestroy = True

		eventData = EvIface(iface)
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
		this.iface = {}
		this.ref = {}

	def importJSON(this, json, options: Dict={}):
		if(isinstance(json, str)):
			json = JSON.loads(json)

		appendMode = 'appendMode' in options and options['appendMode'] == False
		if(not appendMode): this.clearNodes()
		reorderInputPort = []
		this._importing = True

		# Do we need this?
		# this.emit("json.importing",:appendMode: options.appendMode, raw: json})

		metadata = None
		if('_' in json):
			metadata = json['_']
			del json['_']
		
		if(metadata != None):
			if('env' in metadata):
				Environment.imports(metadata['env'])

			if('functions' in metadata):
				functions = metadata['functions']
	
				for key, value in functions.items():
					this.createFunction(key, value)

	
			if('variables' in metadata):
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
		for namespace, ifaces in json.items():
			# Every ifaces that using this namespace name
			for ifaceJSON in ifaces:
				iface = inserted[ifaceJSON['i']]

				if('route' in ifaceJSON):
					iface.node.routes.routeTo(inserted[ifaceJSON['route']['i']])

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
									raise Exception(f"Can't create output port ({portName}) for function ({iface._funcMain.node._funcInstance.id})")

							elif(iface._enum == Enums.BPVarGet):
								target = this._getTargetPortType(this, 'input', ports)
								iface.useType(target)
								linkPortA = iface.output[portName]

							else: raise Exception(f"Node port not found for iface (index: {ifaceJSON['i']}, title: {iface.title}), with port name: {portName}")

						# Current output's available targets
						for target in ports:
							target['i'] += appendLength
							targetNode = inserted[target['i']]

							# output can only meet input port
							linkPortB = targetNode.input.get(target['name'])
							if(linkPortB == None):
								if(targetNode._enum == Enums.BPFnOutput):
									linkPortB = targetNode.addPort(linkPortA, target['name'])

									if(linkPortB == None):
										raise Exception(f"Can't create output port ({target['name']}) for function ({targetNode._funcMain.node._funcInstance.id})")

								elif(targetNode._enum == Enums.BPVarSet):
									targetNode.useType(linkPortA)
									linkPortB = targetNode.input[target['name']]

								elif(linkPortA.type == PortType.Route):
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
		# this.emit("json.imported", {appendMode: options.appendMode, nodes: inserted, raw: json})
		this.executionOrder.next()

		return inserted

	def settings(this, which, val):
		if(val == None):
			return this.settings[which]

		this.settings[which] = val

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

	def createNode(this, namespace, options=None, nodes=None):
		func = Internal.nodes.get(namespace)

		# Try to load from registered namespace folder if exist
		funcNode = None
		if(namespace.startswith("BPI/F/")):
			func = this.functions.get(namespace[6:])

			if(func != None):
				funcNode = func.node(this)

		if(func == None):
			raise Exception(f"Node nodes for namespace '{namespace}' was not found, maybe .registerNode() haven't being called?")

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

			parent = iface.node._funcInstance
			if(parent != None):
				parent.rootInstance.ref[iface.id] = iface.ref

		if(options['i'] != None):
			iface.i = options['i']

			ii = len(this.ifaceList)
			while ii <= iface.i:
				ii += 1
				this.ifaceList.append(None)

			this.ifaceList[iface.i] = iface

		else: this.ifaceList.append(iface)

		if('input_d' in options):
			defaultInputData = options['input_d']
			if(defaultInputData != None):
				iface._importInputs(defaultInputData)

		savedData = options['data'] if 'data' in options else None
		portSwitches = options['output_sw'] if 'output_sw' in options else None

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
		if(id in this.variables):
			this.variables[id].destroy()
			del this.variables[id]

		# deepProperty

		# BPVariable = ./nodes/Var.js
		temp = BPVariable(id, options)
		this.variables[id] = temp
		this.emit('variable.new', temp)

		return temp

	def createFunction(this, id, options):
		if(id in this.functions):
			this.functions[id].destroy()
			del this.functions[id]

		# BPFunction = ./nodes/Fn.js
		temp = BPFunction(id, options, this)
		this.functions[id] = temp

		if('vars' in options):
			vars = options['vars']
			for val in vars:
				temp.createVariable(val, {"scope": VarScope.shared})

		if('privateVars' in options):
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

Internal.interface['BP/default'] = Interface