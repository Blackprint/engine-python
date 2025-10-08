from ..Internal import EvPortSelf, EvPortValue, EvCable
from ..Utils import Utils
from ..Types import Types

from typing import TYPE_CHECKING
if TYPE_CHECKING:
	from .Port import Port

class Cable:
	def __init__(this, owner, target):
		this.type = owner.type
		this.owner: 'Port' = owner
		this.target: 'Port' = target
		this.source = owner.source

		if(owner.source == 'input'):
			inp = owner
			out = target

		else:
			inp = target
			out = owner

		this.input: 'Port' = inp
		this.output: 'Port' = out

		this.disabled = False
		this.isRoute = False
		this.connected = False
		this._hasUpdate = False
		this._ghost = False
		this._disconnecting = False
		this._calling = False

		# For remote-control
		this._evDisconnected = False

	def connecting(this):
		if(this.disabled or this.input.type == Types.Slot or this.output.type == Types.Slot):
			# inp.iface.node.instance.emit('cable.connecting', {
			# 	port: input, target: output
			# });
			return

		this.connected()

	def _connected(this):
		inp = this.input
		out = this.output
		this.connected = True

		# Skip event emit or node update for route cable connection
		if(this.isRoute): return

		tempEv = EvPortValue(inp, out, this)
		inp.emit('cable.connect', tempEv)
		inp.iface.emit('cable.connect', tempEv)

		tempEv2 = EvPortValue(out, inp, this)
		out.emit('cable.connect', tempEv2)
		out.iface.emit('cable.connect', tempEv2)

		inp.iface.node.instance.emit('cable.connect', tempEv)
		inp.emit('connect', tempEv)
		out.emit('connect', tempEv2)

		if(out.value != None):
			input = this.input
			input.emit('value', tempEv)
			input.iface.emit('port.value', tempEv)

			node = input.iface.node
			if(node.instance._importing):
				node.instance.executionOrder.add(node, this)
			elif(len(node.routes.inp) == 0):
				Utils.runAsync(node._bpUpdate(this))

	# For debugging
	def _print(this):
		print(f"\nCable: {this.output.iface.title}.{this.output.name} . {this.input.name}.{this.input.iface.title}")

	def visualizeFlow(this):
		instance = this.owner.iface.node.instance
		if(instance._remote != None):
			instance._emit('_flowEvent', EvCable(this))

	@property
	def value(this):
		if(this._disconnecting): return this.input.default
		this.visualizeFlow()
		return this.output.value

	def disconnect(this, which=False): # which = port
		owner = this.owner
		target = this.target

		if(this.isRoute): # ToDo: simplify, use 'which' instead of check all
			output = this.output

			if(output == None): return

			if(output.out == this): output.out = None
			elif(this.input.out == this): this.input.out = None

			i = Utils.findFromList(output.inp, this)
			if(i != None):
				output.inp.pop(i)
			elif(this.input != None):
				i = Utils.findFromList(this.input.inp, this)
				if(i != None):
					this.input.inp.pop(i)

			this.connected = False

			if(target == None): return # Skip disconnection event emit

			temp1 = EvPortValue(owner, target, this)
			owner.emit('disconnect', temp1)
			owner.iface.emit('cable.disconnect', temp1)
			owner.iface.node.instance.emit('cable.disconnect', temp1)

			if(target == None): return
			temp2 = EvPortValue(target, owner, this)
			target.emit('disconnect', temp2)
			target.iface.emit('cable.disconnect', temp2)

			return

		alreadyEmitToInstance = False
		this._disconnecting = True

		inputPort = this.input
		if(inputPort != None):
			oldVal = this.output.value
			inputPort._cache = None

			defaultVal = inputPort.default
			if(defaultVal != None and defaultVal != oldVal):
				iface = inputPort.iface
				node = iface.node
				routes = node.routes; # PortGhost's node may not have routes

				if(iface._bpDestroy != True and routes != None and len(routes.inp) == 0):
					temp = EvPortValue(inputPort, this.output, this)
					inputPort.emit('value', temp)
					iface.emit('port.value', temp)
					node.instance.executionOrder.add(node)

			inputPort._hasUpdateCable = None

		# Remove from cable owner
		if(owner and (not which or owner == which)):
			i = Utils.findFromList(owner.cables, this)
			if(i != None):
				owner.cables.pop(i)

			if(this.connected):
				temp = EvPortValue(owner, target, this)
				owner.emit('disconnect', temp)
				owner.iface.emit('cable.disconnect', temp)
				owner.iface.node.instance.emit('cable.disconnect', temp)

				alreadyEmitToInstance = True
			else:
				temp = EvPortValue(owner, None, this)
				owner.iface.emit('cable.cancel', temp)
				# owner.iface.node.instance.emit('cable.cancel', temp)

		# Remove from connected target
		if(target and this.connected and (not which or target == which)):
			i = Utils.findFromList(target.cables, this)
			if(i != None):
				target.cables.pop(i)

			temp = EvPortValue(target, owner, this)
			target.emit('disconnect', temp)
			target.iface.emit('cable.disconnect', temp)

			if(not alreadyEmitToInstance):
				target.iface.node.instance.emit('cable.disconnect', temp)

		if(owner or target): this.connected = False
		this._disconnecting = False