from ..Node import Node
from ..Interface import Interface
from ..Nodes.Enums import Enums
from ..Constructor.Port import Port as PortClass
from ..Utils import Utils
from ..Internal import registerNode, registerInterface
from ..Types import Types
from ..Port.PortFeature import Port
from .BPVariable_init import BPVariable, VarScope

# Don't delete even unused, this is needed for importing the internal node
from .Environments import BPEnvGet

@registerNode('BP/Var/Set')
class VarSet(Node):
	input = {}
	iface: 'IVarSet' = None
	def __init__(this, instance):
		Node.__init__(this, instance)
		iface = this.setInterface('BPIC/BP/Var/Set')

		# Specify data field from here to make it enumerable and exportable
		iface.data = {
			"name": '',
			"scope": VarScope.public
		}

		iface.title = 'VarSet'
		iface.type = 'bp-var-set'
		iface._enum = Enums.BPVarSet

	def update(this, cable):
		this.iface._bpVarRef.value = this.input['Val']

	def destroy(this): this.iface.destroyIface()


@registerNode('BP/Var/Get')
class VarGet(Node):
	output = {}
	def __init__(this, instance):
		Node.__init__(this, instance)
		iface = this.setInterface('BPIC/BP/Var/Get')

		# Specify data field from here to make it enumerable and exportable
		iface.data = {
			"name": '',
			"scope": VarScope.public
		}

		iface.title = 'VarGet'
		iface.type = 'bp-var-get'
		iface._enum = Enums.BPVarGet

	def destroy(this): this.iface.destroyIface()

class BPVarGetSet(Interface):
	_onChanged = None
	_dynamicPort = True # Port is initialized dynamically

	def imported(this, data):
		if(('scope' not in data) or ('name' not in data)):
			raise Exception("'scope' and 'name' options is required for creating variable node")

		this.changeVar(data['name'], data['scope'])
		temp = this._bpVarRef
		temp.used.append(this)

	def changeVar(this, name, scopeId):
		if(this.data['name'] != ''):
			raise Exception("Can't change variable node that already be initialized")
			
		this.data['name'] = name
		this.data['scope'] = scopeId

		_funcInstance = this.node.instance._funcMain
		if(_funcInstance != None):
			_funcInstance = _funcInstance.node._funcInstance

		if(scopeId == VarScope.public):
			if(_funcInstance != None):
				scope = _funcInstance.rootInstance.variables
			else: scope = this.node.instance.variables

		elif(scopeId == VarScope.shared):
			scope = _funcInstance.variables
		else: # private
			scope = this.node.instance.variables

		construct = Utils.getDeepProperty(scope, name.split('/'))

		if(construct == None):
			if(scopeId == VarScope.public): _scopeName = 'public'
			elif(scopeId == VarScope.private): _scopeName = 'private'
			elif(scopeId == VarScope.shared): _scopeName = 'shared'
			else: _scopeName = 'unknown'

			raise Exception(f"'{name}' variable was not defined on the '{_scopeName} (scopeId: {scopeId})' instance")

		return construct

	def _reinitPort(this):
		raise Exception("It should only call child method and not the parent")

	def useType(this, port: PortClass):
		temp = this._bpVarRef
		if(temp.type != Types.Slot):
			if(port == None): temp.type = Types.Slot
			return

		if(port == None): raise Exception("Can't set type with None")
		temp.type = port._config if port._config != None else port.type
		if(isinstance(temp, dict) and temp.type['feature'] == Port.Trigger):
			temp.type = Types.Trigger

		if(port.type == Types.Slot):
			this.waitTypeChange(temp, port)
		else:
			this._recheckRoute()
			temp.emit('type.assigned')

		# Also create port for other node that using this variable
		used = temp.used
		for item in used:
			item._reinitPort()

	def waitTypeChange(this, bpVar, port=None):
		def callback():
			if(port != None):
				bpVar.type = port._config if port._config != None else port.type
				if(isinstance(bpVar, dict) and bpVar.type['feature'] == Port.Trigger):
					bpVar.type = Types.Trigger

				bpVar.emit('type.assigned')
			else:
				if this.input['Val'] != None:
					target = this.input['Val']
				else: target = this.output['Val']
				target.assignType(bpVar.type)

			this._recheckRoute()

		this._waitTypeChange = callback
		this._destroyWaitType = lambda: bpVar.off('type.assigned', this._waitTypeChange)

		iPort = port if port != None else bpVar
		iPort.once('type.assigned', this._waitTypeChange)

	def _recheckRoute(this):
		if(
			(hasattr(this, 'input') and ('Val' in this.input) and this.input['Val'].type == Types.Trigger)
     		or
			(hasattr(this, 'output') and ('Val' in this.output) and this.output['Val'].type == Types.Trigger)
		):
			routes = this.node.routes
			routes.disableOut = True
			routes.noUpdate = True

	def destroyIface(this):
		temp = this._destroyWaitType
		if(temp != None):
			this._destroyWaitType()

		temp = this._bpVarRef
		if(temp == None): return

		i = Utils.findFromList(temp.used, this)
		if(i != None): temp.used.pop(i)

		listener = this._bpVarRef.listener
		if(listener == None): return

		i = Utils.findFromList(listener, this)
		if(i != None): listener.pop(i)

@registerInterface('BPIC/BP/Var/Get')
class IVarGet(BPVarGetSet):
	_eventListen = None
	def changeVar(this, name, scopeId):
		if(this.data['name'] != ''):
			raise Exception("Can't change variable node that already be initialized")

		if(this._onChanged != None):
			if(this._bpVarRef != None):
				this._bpVarRef.off('value', this._onChanged)

		varRef = BPVarGetSet.changeVar(this, name, scopeId)
		this.title = name.replace('/', ' / ')

		this._bpVarRef = varRef
		if(varRef.type == Types.Slot): return

		this._reinitPort()
		this._recheckRoute()

	def _reinitPort(this):
		temp = this._bpVarRef
		node = this.node

		if(temp.type == Types.Slot):
			this.waitTypeChange(temp)

		if('Val' in this.output):
			node.deletePort('output', 'Val')

		ref = node.output
		node.createPort('output', 'Val', temp.type)

		if(temp.type == Types.Trigger):
			this._eventListen = 'call'
			def callback(ev): ref['Val']()
			this._onChanged = callback
		else:
			this._eventListen = 'value'
			def callback(ev): ref['Val'] = temp._value
			this._onChanged = callback

		if(temp.type != Types.Trigger):
			node.output['Val'] = temp._value

		temp.on(this._eventListen, this._onChanged)
		return this.output['Val']

	def destroyIface(this):
		if(this._eventListen != None):
			this._bpVarRef.off(this._eventListen, this._onChanged)

		BPVarGetSet.destroyIface(this)

@registerInterface('BPIC/BP/Var/Set')
class IVarSet(BPVarGetSet):
	def changeVar(this, name, scopeId):
		varRef = BPVarGetSet.changeVar(this, name, scopeId)
		this.title = name.replace('/', ' / ')

		this._bpVarRef = varRef
		if(varRef.type == Types.Slot): return

		this._reinitPort()
		this._recheckRoute()

	def _reinitPort(this):
		input = this.input
		node = this.node
		temp = this._bpVarRef

		if(temp.type == Types.Slot):
			this.waitTypeChange(temp)

		if('Val' in input):
			node.deletePort('input', 'Val')

		if(temp.type == Types.Trigger):
			node.createPort('input', 'Val', Port.Trigger(lambda port: temp.emit('call')))

		else: node.createPort('input', 'Val', temp.type)

		return input['Val']