import asyncio
from ..Port.PortFeature import Port as PortFeature
from ..Nodes.Enums import Enums
import traceback

class EvExecutionPaused:
	def __init__(this, afterNode, beforeNode, cable, cables, triggerSource):
		this.afterNode = afterNode
		this.beforeNode = beforeNode
		this.cable = cable
		this.cables = cables

		# 0 = execution order, 1 = route, 2 = trigger port, 3 = request
		# execution priority: 3, 2, 1, 0
		this.triggerSource = triggerSource

class OrderedExecution:
	index = 0
	length = 0
	initialSize = 30
	pause = False
	stepMode = False
	_processing = False

	# Pending because stepMode
	_pRequest = []
	_pRequestLast = []
	_pTrigger = []
	_pRoute = []
	_hasStepPending = False
	_tCable = None
	_lastCable = None
	_lastBeforeNode = None

	def __init__(this, instance, size=30):
		this.initialSize = size
		this.instance = instance

		# array<Blackprint.Node>
		this.list = size*[None]

		# Cable who trigger the execution order's update (with stepMode)
		this._tCable = {} # Map { Node : Set<Cable> }

	def isPending(this, node):
		return node in this.list

	def clear(this):
		list = this.list
		for i in range(this.index, this.length):
			list[i] = None

		this.length = this.index = 0

	def add(this, node, _cable=None):
		if(this.isPending(node)):
			# print("pending "+node.iface.title)
			return

		this._isReachLimit()
		# print(f"add {node.iface.title} {node.iface.id}")

		this.list[this.length] = node
		this.length += 1

		if(this.stepMode):
			if(_cable != None): this._tCableAdd(node, _cable)
			this._emitNextExecution()

	def _tCableAdd(this, node, cable):
		tCable = this._tCable # Cable triggerer
		sets = tCable.get(node)
		if(sets == None):
			sets = set() # Set
			tCable.put(node, sets)

		sets.add(cable)

	def _isReachLimit(this):
		i = this.index + 1
		if(i >= this.initialSize or this.length >= this.initialSize):
			raise Exception("Execution order limit was exceeded")

	def _next(this):
		if(this.index >= this.length):
			return

		if(this.stepMode): this._tCable.remove(temp)

		i = this.index
		temp = this.list[i]
		this.list[i] = None
		this.index += 1

		if(this.index >= this.length):
			this.index = this.length = 0

		return temp

	def _emitPaused(this, afterNode, beforeNode, triggerSource, cable, cables=None):
		this.instance._emit('execution.paused', EvExecutionPaused(
			afterNode,
			beforeNode,
			cable,
			cables,
			triggerSource,
		))

	def _addStepPending(this, cable, triggerSource):
		# 0 = execution order, 1 = route, 2 = trigger port, 3 = request
		if(triggerSource == 1 and cable not in this._pRoute): this._pRoute.append(cable)
		if(triggerSource == 2 and cable not in this._pTrigger): this._pTrigger.append(cable)
		if(triggerSource == 3):
			hasCable = False
			list = this._pRequest
			for val in list:
				if(val == cable):
					hasCable = True
					break

			if(hasCable == False):
				cableCall = None
				inputPorts = cable.input.iface.input

				for key, port in inputPorts:
					if(port._calling):
						cables = port.cables
						for _cable in cables:
							if(_cable._calling):
								cableCall = _cable
								break
						break

				list.append({
					'cableCall': cableCall,
					'cable': cable,
				})

		this._hasStepPending = True
		this._emitNextExecution()

	# For step mode
	def _emitNextExecution(this, afterNode=None):
		triggerSource = 0
		beforeNode = None

		if(len(this._pRequest) != 0):
			triggerSource = 3
			cable = this._pRequest[0].cable
		elif(len(this._pRequestLast) != 0):
			triggerSource = 0
			beforeNode = this._pRequestLast[0].node
		elif(len(this._pTrigger) != 0):
			triggerSource = 2
			cable = this._pTrigger[0]
		elif(len(this._pRoute) != 0):
			triggerSource = 1
			cable = this._pRoute[0]

		if(cable != None):
			if(this._lastCable == cable): return # avoid duplicate event trigger

			inputNode = cable.input.iface.node
			outputNode = cable.output.iface.node

		if(triggerSource == 0):
			if(beforeNode == None):
				beforeNode = this.list[this.index]

			# avoid duplicate event trigger
			if(this._lastBeforeNode == beforeNode): return

			cables = this._tCable.get(beforeNode) # Set<Cables>
			if(cables): cables = cables.toArray()

			return this._emitPaused(afterNode, beforeNode, 0, None, cables)
		elif(triggerSource == 3):
			return this._emitPaused(inputNode, outputNode, triggerSource, cable)
		else: return this._emitPaused(outputNode, inputNode, triggerSource, cable)

	def _checkStepPending(this):
		if(not this._hasStepPending): return
		_pRequest = this._pRequest
		_pRequestLast = this._pRequestLast
		_pTrigger = this._pTrigger
		_pRoute = this._pRoute

		if(len(_pRequest) != 0):
			[ cable, cableCall ] = _pRequest.pop(0)
			currentIface = cable.output.iface
			current = currentIface.node

			# cable.visualizeFlow()
			currentIface._requesting = True
			try:
				current.request(cable)
			finally:
				currentIface._requesting = False

			inpIface = cable.input.iface

			# Check if the cable was the last requester from a node
			isLast = True
			for value in _pRequest:
				if(value.cable.input.iface == inpIface):
					isLast = False

			if(isLast):
				this._pRequestLast.append({
					'node': inpIface.node,
					'cableCall': cableCall,
				})

				if(cableCall != None):
					this._tCableAdd(cableCall.input.iface.node, cableCall)

			this._tCableAdd(inpIface.node, cable)
			this._emitNextExecution()
		elif(len(_pRequestLast) != 0):
			[ node, cableCall ] = _pRequestLast.pop()

			cour = node.update(None)
			if(asyncio.iscoroutine(cour)): asyncio.run(cour)

			if(cableCall != None):
				cableCall.input._call(cableCall)

			this._tCable.remove(node)
			this._emitNextExecution()
		elif(len(_pTrigger) != 0):
			cable = _pTrigger.pop(0)
			current = cable.input

			# cable.visualizeFlow()
			current._call(cable)

			this._emitNextExecution()
		elif(len(_pRoute) != 0):
			cable = _pRoute.pop(0)

			# cable.visualizeFlow()
			cable.input.routeIn(cable, True)

			this._emitNextExecution()
		else: return False

		if(len(_pRequest) == 0 and len(_pRequestLast) == 0 and len(_pTrigger) == 0 and len(_pRoute) == 0):
			this._hasStepPending = False

		return True

	def next(this, force=False):
		# asyncio.sleep(0)

		if(this._processing): return
		if(this.pause and not force): return
		if(this._checkStepPending()): return
		if(this.stepMode): this.pause = True

		next = this._next() # next: node
		if(next == None): return

		this._processing = True

		_proxyInput = None
		nextIface = next.iface
		next._bpUpdating = True

		if(next.partialUpdate):
			next.partialUpdate = False

		skipUpdate = len(next.routes.inp) != 0
		if(nextIface._enum == Enums.BPFnMain):
			_proxyInput = nextIface._proxyInput
			_proxyInput._bpUpdating = True

		# print(f"run {next.iface.title} {next.iface.id}")

		try:
			if(next.partialUpdate):
				portList = nextIface.input
				for inp in portList:
					if(inp.feature == PortFeature.ArrayOf):
						if(inp._hasUpdate != False):
							inp._hasUpdate = False
	
							if(not skipUpdate):
								cables = inp.cables
								for cable in cables:
									if(not cable._hasUpdate): continue
									cable._hasUpdate = False
	
									cour = next.update(cable)
									if(asyncio.iscoroutine(cour)): asyncio.run(cour)

					elif(inp._hasUpdateCable != None):
						cable = inp._hasUpdateCable
						inp._hasUpdateCable = None
	
						if(not skipUpdate):
							cour = next.update(cable)
							if(asyncio.iscoroutine(cour)): asyncio.run(cour)

			next._bpUpdating = False
			if(_proxyInput): _proxyInput._bpUpdating = False

			if(not next.partialUpdate and not skipUpdate): next._bpUpdate()
		except:
			if(_proxyInput): _proxyInput._bpUpdating = False
			this.clear()
			traceback.print_exc()

		if(this.stepMode): this._emitNextExecution = next
		this._processing = False
		this.next()