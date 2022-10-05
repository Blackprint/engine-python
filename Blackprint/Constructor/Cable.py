from ..Internal import EvPortSelf, EvPortValue
from ..Utils import Utils

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

		# For remote-control
		this._evDisconnected = False

	def _connected(this):
		owner = this.owner
		target = this.target
		this.connected = True

		# Skip event emit or node update for route cable connection
		if(this.isRoute): return

		temp = EvPortValue(owner, target, this)
		owner.emit('cable.connect', temp)
		owner.iface.emit('cable.connect', temp)

		temp2 = EvPortValue(target, owner, this)
		target.emit('cable.connect', temp2)
		target.iface.emit('cable.connect', temp2)

		if(this.output.value == None): return

		tempEv = EvPortSelf(this.output)
		input = this.input
		input.emit('value', tempEv)
		input.iface.emit('port.value', tempEv)

		node = input.iface.node
		if(node.instance._importing):
			node.instance.executionOrder.add(node)
		else: Utils.runAsync(node._bpUpdate())

	# For debugging
	def _print(this):
		print(f"\nCable: {this.output.iface.title}.{this.output.name} . {this.input.name}.{this.input.iface.title}")

	@property
	def value(this):
		return this.output.value

	def disconnect(this, which=False): # which = port
		if(this.isRoute): # ToDo: simplify, use 'which' instead of check all
			input = this.input
			output = this.output

			if(output.cables != None): output.cables.clear()
			elif(output.out == this): output.out = None
			elif(input.out == this): input.out = None

			i = Utils.findFromList(output.inp, this)
			if(i != -1):
				output.inp.pop(i)

			elif(input != None):
				i = Utils.findFromList(input.inp, this)
				if(i != -1):
					input.inp.pop(i)

			this.connected = False
			return

		owner = this.owner
		target = this.target
		alreadyEmitToInstance = False

		if(this.input != None):
			this.input._cache = None

		# Remove from cable owner
		if(owner and (not which or owner == which)):
			i = Utils.findFromList(owner.cables, this)
			if(i != -1):
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
			if(i != -1):
				target.cables.pop(i)

			temp = EvPortValue(target, owner, this)
			target.emit('disconnect', temp)
			target.iface.emit('cable.disconnect', temp)

			if(not alreadyEmitToInstance):
				target.iface.node.instance.emit('cable.disconnect', temp)

		# if(hasOwner or hasTarget) this.connected = False