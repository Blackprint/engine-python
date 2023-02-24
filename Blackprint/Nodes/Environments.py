from ..Environment import Environment
from ..Node import Node
from ..Interface import Interface
from ..Event import Event
from .Enums import Enums
from ..Internal import registerNode, registerInterface

@registerNode('BP/Env/Get')
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

	def destroy(this): this.iface.destroyListener()

@registerNode('BP/Env/Set')
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
		Environment.set(this.iface.data['name'], this.input["Val"])

	def destroy(this): this.iface.destroyListener()

class BPEnvGetSet(Interface):
	def imported(this, data):
		if('name' not in data or data['name'] == ''): raise Exception("Parameter 'name' is required")
		this.data['name'] = data['name']

		# Create environment if not exist
		if(data['name'] not in Environment.map):
			Environment.set(data['name'], '')

		name = this.data['name']
		rules = Environment._rules[name] if name in Environment._rules else None

		# Only allow connection to certain node namespace
		if(rules != None):
			if(this._enum == Enums.BPEnvGet and 'allowGet' in rules):
				Val = this.output['Val']
				def callback(cable, targetPort):
					if(targetPort.iface.namespace not in rules['allowGet']):
						Val._cableConnectError('cable.rule.disallowed', {
							"cable": cable,
							"port": Val,
							"target": targetPort
						})
						cable.disconnect()
						return True # Disconnect cable or disallow connection
				Val.onConnect = callback

			elif(this._enum == Enums.BPEnvSet and 'allowSet' in rules):
				Val = this.input['Val']
				def callback(cable, targetPort):
					if(targetPort.iface.namespace not in rules['allowSet']):
						Val._cableConnectError('cable.rule.disallowed', {
							"cable": cable,
							"port": Val,
							"target": targetPort
						})
						cable.disconnect()
						return True # Disconnect cable or disallow connection
				Val.onConnect = callback

	def destroyListener():
		# if(this._nameListener == None): return
		# Blackprint.off('environment.renamed', this._nameListener)
		pass

@registerInterface('BPIC/BP/Env/Get')
class IEnvGet(BPEnvGetSet):
	_listener = None
	def imported(this, data):
		BPEnvGetSet.imported(this, data)
		def _listener(v):
			if(v.key != this.data['name']): return # use full $this.data.name
			this.ref.Output["Val"] = v.value

		this._listener = _listener

		Event.on('environment.changed environment.added', _listener)
		this.ref.Output["Val"] = Environment.map[this.data['name']]

	def destroyListener(this):
		if(this._listener == None): return
		Event.off('environment.changed environment.added', this._listener)


@registerInterface('BPIC/BP/Env/Set')
class IEnvSet(BPEnvGetSet):
	def _nothing(): pass