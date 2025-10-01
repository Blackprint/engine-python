from ..Constructor.CustomEvent import CustomEvent
from ..Types import Types
import re

# For internal library use only
class VarScope:
	Public = 0
	Private = 1
	Shared = 2

# used for instance.createVariable
class BPVariable(CustomEvent):
	type = None
	bpFunction = None  # Only exist for function node's variable (shared/private)

	def __init__(this, id, options={}):
		CustomEvent.__init__(this)

		id = re.sub(r'/^\/|\/$/m', '', id)
		id = re.sub(r'/[`~!@#$%^&*()\-_+={}\[\]:"|;\'\\\\,.<>?]+/', '_', id)
		this.id = id
		this.title = options['title'] if 'title' in options else id

		# The type need to be defined dynamically on first cable connect
		this.type = Types.Slot
		this.used = []  # [Interface, Interface, ...]

		this.totalSet = 0
		this.totalGet = 0
		this._value = None

	@property
	def value(this):
		return this._value

	@value.setter
	def value(this, val):
		if(this._value == val): return

		this._value = val
		this.emit('value')

	def destroy(this):
		map = this.used  # This list can be altered multiple times when deleting a node
		for iface in list(map):  # Create a copy to avoid modification during iteration
			iface.node.instance.deleteNode(iface)

		this.emit('destroy')
