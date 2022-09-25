from .. import Types, Environment, Node, Interface
from . import Enums
import Blackprint

@Blackprint.registerNode('BP/Env/Get')
class BPEnvGet(Node):
	output = {"Val": str}
	def __init__(this, instance):
		Node.__init__(this, instance)
		iface = this.setInterface('BPIC/BP/Env/Get')

		# Specify data field from here to make it enumerable and exportable
		iface.data = {"name": ''}
		iface.title = 'EnvGet'
		iface.type = 'bp-env-get'

		iface._enum = Enums.BPEnvGet

@Blackprint.registerNode('BP/Env/Set')
class BPEnvSet(Node):
	input = {"Val": str}

	def __init__(this, instance):
		Node.__init__(this, instance)
		iface = this.setInterface('BPIC/BP/Env/Set')
		
		# Specify data field from here to make it enumerable and exportable
		iface.data = {"name": ''}
		iface.title = 'EnvSet'
		iface.type = 'bp-env-set'

		iface._enum = Enums.BPEnvSet

	def update(this, cable):
		Environment.set(this.iface.data['name'], this.input["Val"]())

class BPEnvGetSet(Interface):
	def imported(this, data):
		if(not data['name']): raise Exception("Parameter 'name' is required")
		this.data['name'] = data['name']

		# Create environment if not exist
		if(not Environment.map.has_key(data['name'])):
			Environment.set(data['name'], '')

@Blackprint.registerInterface('BPIC/BP/Env/Get')
class IEnvGet(BPEnvGetSet):
	def imported(this, data):
		BPEnvGetSet.imported(this, data)
		def _listener(v):
			if(v.key != this.data['name']): return
			this.ref.Output["Val"](v.value)

		this._listener = _listener

		Blackprint.Event.on('environment.changed environment.added', _listener)
		this.ref.Output["Val"](Environment.map[this.data['name']])

	def destroy(this):
		if(this._listener == None): return
		Blackprint.Event.off('environment.changed environment.added', this._listener)


@Blackprint.registerInterface('BPIC/BP/Env/Set')
class IEnvSet(BPEnvGetSet):
	def _nothing(): pass