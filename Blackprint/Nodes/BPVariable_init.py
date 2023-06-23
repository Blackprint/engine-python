from ..Constructor.CustomEvent import CustomEvent
from ..Types import Types
import re

# For internal library use only
class VarScope:
	public = 0
	private = 1
	shared = 2

# used for instance.createVariable
class BPVariable(CustomEvent):
	type = None
	# this.totalSet = 0
	# this.totalGet = 0

	def __init__(this, id, options={}):
		CustomEvent.__init__(this)

		id = re.sub(r'/^\/|\/$/m', '', id)
		id = re.sub(r'/[`~!@#$%^&*()\-_+={}\[\]:"|;\'\\\\,.<>?]+/', '_', id)
		this.id = id
		this.title = options['title'] if 'title' in options else id

		# this.rootInstance = instance
		this.id = this.title = id
		this.type = Types.Slot
		this._value = None
		this.isShared = False
		this.used = []

		# The type need to be defined dynamically on first cable connect

	@property
	def value(this):
		return this._value

	@value.setter
	def value(this, val):
		if(this._value == val): return

		this._value = val
		this.emit('value')

	def destroy(this):
		map = this.used
		for iface in map:
			iface.node.instance.deleteNode(iface)

		map.clear()
