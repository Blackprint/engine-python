import asyncio
from ..Port.PortFeature import Port as PortFeature
from ..Nodes.Enums import Enums
import traceback

class OrderedExecution:
	index = 0
	length = 0
	initialSize = 30
	pause = False
	stepMode = False
	_processing = False

	def __init__(this, size=30):
		this.initialSize = size

		# array<Blackprint.Node>
		this.list = size*[None]

	def isPending(this, node):
		return node in this.list

	def clear(this):
		list = this.list
		for i in range(this.index, this.length):
			list[i] = None

		this.length = this.index = 0

	def add(this, node):
		if(this.isPending(node)):
			# print("pending "+node.iface.title)
			return
		
		# print(f"add {node.iface.title} {node.iface.id}")

		i = this.index + 1
		if(i >= this.initialSize or this.length >= this.initialSize):
			raise Exception("Execution order limit was exceeded")

		this.list[this.length] = node
		this.length += 1

	def _next(this):
		if(this.index >= this.length):
			return

		i = this.index
		temp = this.list[i]
		this.list[i] = None
		this.index += 1

		if(this.index >= this.length):
			this.index = this.length = 0

		return temp

	def next(this):
		# asyncio.sleep(0)

		if(this._processing): return
		if(this.pause): return
		if(this.stepMode): this.pause = True

		next = this._next() # next: node
		if(next == None): return

		this._processing = True

		_proxyInput = None
		nextIface = next.iface
		next._bpUpdating = True

		if(next.partialUpdate and next.update == None):
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

		if(this.stepMode): this.pause = False
		this._processing = False
		this.next()