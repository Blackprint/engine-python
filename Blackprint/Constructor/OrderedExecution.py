from ..Port.PortFeature import PortFeature
from ..Nodes.Enums import Enums

class OrderedExecution:
	index = 0
	length = 0
	initialSize = 30
	pause = False
	stepMode = False


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
		if(this.isPending(node)): return

		i = this.index + 1
		if(i >= this.initialSize or this.length >= this.initialSize):
			raise Exception("Execution order limit was exceeded")

		this.length += 1
		this.list[this.length] = node

	def _next(this):
		if(this.index >= this.length):
			return

		i = this.index
		this.index += 1
		temp = this.list[this.index]
		this.list[i] = None

		if(this.index >= this.length):
			this.index = this.length = 0

		return temp

	# Can be async function if the programming language support it
	def next(this):
		if(this.pause): return
		if(this.stepMode): this.pause = True

		next = this._next() # next: node
		if(next == None): return

		_proxyInput = None
		nextIface = next.iface
		next._bpUpdating = True

		if(next.partialUpdate and next.update == None):
			next.partialUpdate = False

		skipUpdate = len(next.routes.inp) != 0
		if(nextIface._enum == Enums.BPFnMain):
			_proxyInput = nextIface._proxyInput
			_proxyInput._bpUpdating = True

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
	
									# Make this async if possible
									next.update(cable)

					elif(inp._hasUpdateCable != None):
						cable = inp._hasUpdateCable
						inp._hasUpdateCable = None
	
						# Make this async if possible
						if(not skipUpdate): next.update(cable)

			next._bpUpdating = False
			if(_proxyInput): _proxyInput._bpUpdating = False

			# Make this async if possible
			if(not next.partialUpdate and not skipUpdate): next._bpUpdate()
		except:
			if(_proxyInput): _proxyInput._bpUpdating = False
			this.clear()
		finally:
			if(this.stepMode): this.pause = False