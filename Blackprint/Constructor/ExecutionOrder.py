import asyncio
from ..Port.PortFeature import Port as PortFeature
from ..Nodes.Enums import Enums
from ..Internal import EvExecutionTerminated
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

class ExecutionOrder:
	index = 0
	lastIndex = 0
	initialSize = 30
	pause = False
	stepMode = False
	_processing = False
	stop = False
	_rootExecOrder = {'stop': False}

	# Pending because stepMode
	_pRequest = []
	_pRequestLast = []
	_pTrigger = []
	_pRoute = []
	_hasStepPending = False
	_tCable = None
	_lastCable = None
	_lastBeforeNode = None
	_execCounter = None
	_lockNext = False
	_nextLocked = False

	def __init__(this, instance, size=30):
		this.instance = instance
		this.initialSize = size
		this.list = size*[None]
		this.index = 0
		this.lastIndex = 0
		this.stop = False
		this.pause = False
		this.stepMode = False
		this._lockNext = False
		this._nextLocked = False
		this._execCounter = None
		this._rootExecOrder = {'stop': False}

		# Cable who trigger the execution order's update (with stepMode)
		this._tCable = {} # Map { Node : Set<Cable> }

	def isPending(this, node=None):
		if this.index == this.lastIndex: return False
		if node == None: return True
		return node in this.list

	def clear(this):
		list = this.list
		for i in range(this.index, this.lastIndex):
			list[i] = None

		this.lastIndex = this.index = 0

	def add(this, node, _cable=None):
		if(this.stop or this._rootExecOrder['stop'] or this.isPending(node)):
			return

		this._isReachLimit()

		this.list[this.lastIndex] = node
		this.lastIndex += 1

		if(this.stepMode):
			if(_cable != None): this._tCableAdd(node, _cable)
			this._emitNextExecution()

	def _tCableAdd(this, node, cable):
		if(this.stop or this._rootExecOrder['stop']):
			return

		tCable = this._tCable # Cable triggerer
		sets = tCable.get(node)
		if(sets == None):
			sets = set() # Set
			tCable[node] = sets

		sets.add(cable)

	def _isReachLimit(this):
		i = this.index + 1
		if(i >= this.initialSize or this.lastIndex >= this.initialSize):
			raise Exception("Execution order limit was exceeded")

	def _next(this):
		if(this.stop or this._rootExecOrder['stop']):
			return
		if(this.index >= this.lastIndex):
			return

		i = this.index
		temp = this.list[i]
		this.list[i] = None
		this.index += 1

		if(this.stepMode):
			if temp in this._tCable:
				this._tCable.remove(temp)

		if(this.index >= this.lastIndex):
			this.index = this.lastIndex = 0

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
		if(this.stop or this._rootExecOrder['stop']):
			return

		# 0 = execution order, 1 = route, 2 = trigger port, 3 = request
		if(triggerSource == 1 and cable not in this._pRoute): this._pRoute.append(cable)
		if(triggerSource == 2 and cable not in this._pTrigger): this._pTrigger.append(cable)
		if(triggerSource == 3):
			hasCable = False
			list = this._pRequest
			for val in list:
				if(val['cable'] == cable):
					hasCable = True
					break

			if(hasCable == False):
				cableCall = None
				inputPorts = cable.input.iface.input

				for key, port in inputPorts.items():
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
		if(this.stop or this._rootExecOrder['stop']):
			return

		triggerSource = 0
		beforeNode = None
		cable = None
		inputNode = None
		outputNode = None

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
			if(cables):
				cables = list(cables)

			return this._emitPaused(afterNode, beforeNode, 0, None, cables)
		elif(triggerSource == 3):
			return this._emitPaused(inputNode, outputNode, triggerSource, cable)
		else: return this._emitPaused(outputNode, inputNode, triggerSource, cable)

	def _checkExecutionLimit(this):
		limit = this.instance._settings.get('singleNodeExecutionLoopLimit')
		if(not limit):
			this._execCounter = None
			return

		if(this.lastIndex - this.index == 0):
			if(this._execCounter != None):
				this._execCounter.clear()
			return

		node = this.list[this.index]
		if(node == None):
			raise Exception("Empty")

		if(this._execCounter == None):
			this._execCounter = {}

		if(node not in this._execCounter):
			this._execCounter[node] = 0

		count = this._execCounter[node] + 1
		this._execCounter[node] = count

		if(count > limit):
			print(f"Execution terminated at {node.iface}")
			this.stepMode = True
			this.pause = True
			this._execCounter.clear()

			message = f"Single node execution loop exceeded the limit ({limit}): {node.iface.namespace}"
			this.instance._emit('execution.terminated', EvExecutionTerminated(message, node.iface))
			return True

	async def _checkStepPending(this):
		if(this.stop or this._rootExecOrder['stop']):
			return
		if(this._checkExecutionLimit()):
			return

		if(not this._hasStepPending): return
		_pRequest = this._pRequest
		_pRequestLast = this._pRequestLast
		_pTrigger = this._pTrigger
		_pRoute = this._pRoute

		if(len(_pRequest) != 0):
			item = _pRequest.pop(0)
			cable = item['cable']
			cableCall = item['cableCall']
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
				if(value['cable'].input.iface == inpIface):
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
			item = _pRequestLast.pop()
			node = item['node']
			cableCall = item['cableCall']

			temp = node.update(None)
			if(asyncio.iscoroutine(temp)): await temp

			if(cableCall != None):
				cableCall.input._call(cableCall)

			if node in this._tCable:
				this._tCable.remove(node)
			this._emitNextExecution()
		elif(len(_pTrigger) != 0):
			cable = _pTrigger.pop(0)
			current = cable.input

			cable.visualizeFlow()
			current._call(cable)

			this._emitNextExecution()
		elif(len(_pRoute) != 0):
			cable = _pRoute.pop(0)

			cable.visualizeFlow()
			cable.input.routeIn(cable, True)

			this._emitNextExecution()
		else: return False

		if(len(_pRequest) == 0 and len(_pRequestLast) == 0 and len(_pTrigger) == 0 and len(_pRoute) == 0):
			this._hasStepPending = False

		return True

	async def next(this, force=False):
		if(this.stop or this._rootExecOrder['stop'] or this._nextLocked):
			return
		if(this.stepMode): this.pause = True
		if(this.pause and not force): return
		if(len(this.instance.ifaceList) == 0): return
		if(await this._checkStepPending()): return

		next = this._next() # next: node
		if(next == None): return

		skipUpdate = len(next.routes.inp) != 0
		nextIface = next.iface
		next._bpUpdating = True

		if(next.partialUpdate and next.update == None):
			next.partialUpdate = False

		_proxyInput = None
		if(nextIface._enum == Enums.BPFnMain):
			_proxyInput = nextIface._proxyInput
			_proxyInput._bpUpdating = True

		if(this._lockNext): this._nextLocked = True

		try:
			if(next.partialUpdate):
				portList = nextIface.input
				for inp in portList.values():
					if(inp.feature == PortFeature.ArrayOf):
						if(inp._hasUpdate):
							inp._hasUpdate = False

							if(not skipUpdate):
								cables = inp.cables
								for cable in cables:
									if(not cable._hasUpdate): continue
									cable._hasUpdate = False

									temp = next.update(cable)
									if(asyncio.iscoroutine(temp)): await temp

					elif(inp._hasUpdateCable != None):
						cable = inp._hasUpdateCable
						inp._hasUpdateCable = None

						if(not skipUpdate):
							temp = next.update(cable)
							if(asyncio.iscoroutine(temp)): await temp

			next._bpUpdating = False
			if(_proxyInput != None): _proxyInput._bpUpdating = False

			if(not skipUpdate):
				if(not next.partialUpdate): await next._bpUpdate()
				elif(next.bpFunction != None): await next.iface.bpInstance.executionOrder.start()
		except:
			if(_proxyInput != None): _proxyInput._bpUpdating = False
			this.clear()
			traceback.print_exc()
		finally:
			this._nextLocked = False
			if(this.stepMode): this._emitNextExecution(next)

	async def start(this):
		if(this.stop or this._rootExecOrder['stop'] or this._nextLocked or this.pause):
			return

		this._lockNext = True
		for i in range(this.index, this.lastIndex):
			await this.next()
		this._lockNext = False