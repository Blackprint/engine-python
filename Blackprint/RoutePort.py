from .Types import Types
from .Constructor.Cable import Cable
from .Nodes.Enums import Enums

from typing import TYPE_CHECKING
if TYPE_CHECKING:
	from .Interface import Interface

class RoutePort:
	def __init__(this, iface):
		this.inp: list[Cable] = [] # Allow incoming route from multiple path
		this.out: Cable = None # Only one route/path
		this.disableOut = False
		this.disabled = False
		this.isRoute = True
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
		if(cable in this.inp): return False
		if(this.iface.node.update == None):
			cable.disconnect()
			raise Exception("node.update() was not defined for this node")

		this.inp.append(cable)
		cable.input = this
		cable.target = this
		cable._connected()

		return True

	def routeIn(this, cable):
		node = this.iface.node
		node.update(cable)
		node.routes.routeOut()

	def routeOut(this):
		if(this.disableOut): return
		if(this.out == None):
			if(this.iface._enum == Enums.BPFnOutput):
				temp = None
				return this.iface._funcMain.node.routes.routeIn(temp)

			return

		targetRoute = this.out.input
		if(targetRoute == None): return

		_enum = targetRoute.iface._enum
		cable = this.out

		if(_enum == None):
			return targetRoute.routeIn(cable)

		if(_enum == Enums.BPFnMain):
			return targetRoute.iface._proxyInput.routes.routeIn(cable)

		if(_enum == Enums.BPFnOutput):
			_cable = None
			targetRoute.iface.node.update(_cable)
			return targetRoute.iface._funcMain.node.routes.routeOut()

		return targetRoute.routeIn(cable)