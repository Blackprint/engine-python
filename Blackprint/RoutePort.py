import asyncio
from .Types import Types
from .Constructor.Cable import Cable
from .Nodes.Enums import Enums
from .Constructor.CustomEvent import CustomEvent

from typing import TYPE_CHECKING
if TYPE_CHECKING:
	from .Interface import Interface

class RoutePort(CustomEvent):
	def __init__(this, iface):
		CustomEvent.__init__(this)
		this.inp: list[Cable] = [] # Allow incoming route from multiple path
		this.out: Cable = None # Only one route/path
		# this._outTrunk = None // If have branch
		this.disableOut = False
		this.disabled = False
		this.isRoute = True
		this.name = "BPRoute"
		this.source = 'route'
		this.iface: 'Interface' = iface
		this.type = Types.Route
		this._isPaused = False

	# Connect other route port (this .out to other .inp port)
	def routeTo(this, iface: 'Interface' = None):
		if(this.out != None):
			this.out.disconnect()

		if(iface == None): # Route ended
			cable = Cable(this, None)
			cable.isRoute = True
			this.out = cable
			return True

		port = iface.node.routes

		cable = Cable(this, port)
		cable.isRoute = True
		cable.output = this
		this.out = cable
		port.inp.append(cable) # ToDo: check if this empty if the connected cable was disconnected

		cable._connected()
		return True

	# Connect to input route
	def connectCable(this, cable):
		if(not cable.isRoute):
			raise Exception("Cable must be created from route port before can be connected to other route port. Please use .routeTo(interface) instead if possible.")
		if(cable in this.inp): return False
		if(this.iface.node.update == None):
			cable.disconnect()
			raise Exception("node.update() was not defined for this node")

		this.inp.append(cable)
		cable.input = this
		cable.target = this
		cable.isRoute = True
		cable._connected()

		return True

	async def routeIn(this, _cable = None, _force = False):
		node = this.iface.node
		if(node.disablePorts): return

		executionOrder = node.instance.executionOrder
		if(executionOrder.stop or executionOrder._rootExecOrder['stop']): return

		# Add to execution list if the ExecutionOrder is in Step Mode
		if(executionOrder.stepMode and _cable and not _force):
			executionOrder._addStepPending(_cable, 1)
			return

		# node = this.iface.node
		_cable.visualizeFlow()

		if(this.iface._enum != Enums.BPFnInput): await node._bpUpdate()
		else: await node.routes.routeOut()

	async def routeOut(this):
		if(this.disableOut): return

		if(this.iface.node.disablePorts): return
		if(this.out == None):
			if(this.iface._enum == Enums.BPFnOutput):
				return await this.iface.parentInterface.node.routes.routeIn()
			return

		targetRoute = this.out.input
		if(targetRoute == None): return

		_enum = targetRoute.iface._enum

		if(_enum == None):
			return await targetRoute.routeIn(this.out)

		# if(_enum == Enums.BPFnMain):
		# 	return await targetRoute.iface._proxyInput.routes.routeIn(this.out)

		# if(_enum == Enums.BPFnOutput):
		# 	let temp = targetRoute.iface.node._bpUpdate()
		# 	if(temp?.constructor === Promise) await temp; # Performance optimization
		# 	return await targetRoute.iface.parentInterface.node.routes.routeOut()

		return await targetRoute.routeIn(this.out)
