from types import FunctionType
from ..Node import Node
from ..Interface import Interface
from ..Nodes.Enums import Enums
from ..Constructor.CustomEvent import CustomEvent
from ..Constructor.Port import Port as PortClass
from ..Utils import Utils
from ..Internal import registerNode, registerInterface
from ..Types import Types
from ..Port.PortFeature import Port
import re
from .Environments import BPEnvGet # Don't delete, this is needed for importing the internal node

# For internal library use only
class VarScope:
	public = 0
	private = 1
	shared = 2

@registerNode('BP/Var/Set')
class VarSet(Node):
	input = {}
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
		iface._dynamicPort = True # Port is initialized dynamically

	def update(this, cable):
		this.iface._bpVarRef.value = this.input['Val']


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
		iface._dynamicPort = True # Port is initialized dynamically


class BPVarTemp:
	typeNotSet = {'typeNotSet': True} # Flag that a port is not set

# used for instance.createVariable
class BPVariable(CustomEvent):
	type = None
	# this.totalSet = 0
	# this.totalGet = 0

	def __init__(this, id, options=None):
		CustomEvent.__init__(this)

		this.used = []
		id = re.sub(r'[`~!@#$%^&*()\-_+=:}\[\]:"|;\'\\\\,.\/<>?]+', '_', id)

		# this.rootInstance = instance
		this.id = this.title = id
		this.type = BPVarTemp.typeNotSet
		this._value = None

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

class BPVarGetSet(Interface):
	_onChanged = None

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

		if(name not in scope):
			if(scopeId == VarScope.public): _scopeName = 'public'
			elif(scopeId == VarScope.private): _scopeName = 'private'
			elif(scopeId == VarScope.shared): _scopeName = 'shared'
			else: _scopeName = 'unknown'

			raise Exception(f"'{name}' variable was not defined on the '{_scopeName} (scopeId: {scopeId})' instance")

		return scope

	def _reinitPort(this):
		raise Exception("It should only call child method and not the parent")

	
	def useType(this, port: PortClass):
		temp = this._bpVarRef
		if(temp.type != BPVarTemp.typeNotSet):
			if(port == None): temp.type = BPVarTemp.typeNotSet
			return

		if(port == None): raise Exception("Can't set type with None")
		temp.type = port.type

		targetPort = this._reinitPort()
		targetPort.connectPort(port)

		# Also create port for other node that using this variable
		used = temp.used
		for item in used:
			item._reinitPort()

	def destroy(this):
		temp = this._bpVarRef
		if(temp == None): return

		i = Utils.findFromList(temp.used, this)
		if(i != False): temp.used.pop(i)

		listener = this._bpVarRef.listener
		if(listener == None): return

		i = Utils.findFromList(listener, this)
		if(i != False): listener.pop(i)

@registerInterface('BPIC/BP/Var/Get')
class IVarGet(BPVarGetSet):
	def changeVar(this, name, scopeId):
		if(this.data['name'] != ''):
			raise Exception("Can't change variable node that already be initialized")

		if(this._onChanged != None):
			if(this._bpVarRef != None):
				this._bpVarRef.off('value', this._onChanged)

		scope = BPVarGetSet.changeVar(this, name, scopeId)
		this.title = "Get name"

		temp = scope[this.data['name']]
		this._bpVarRef = temp
		if(temp.type == BPVarTemp.typeNotSet): return scope

		this._reinitPort()

	def _reinitPort(this):
		temp = this._bpVarRef
		node = this.node
		if('Val' in this.output):
			node.deletePort('output', 'Val')

		ref = this.node.output
		node.createPort('output', 'Val', temp.type)

		if(temp.type == FunctionType):
			this._eventListen = 'call'
			def callback(ev): ref['Val']()
			this._onChanged = callback
		else:
			this._eventListen = 'value'
			def callback(ev): ref['Val'] = temp._value
			this._onChanged = callback

		temp.on(this._eventListen, this._onChanged)
		return this.output['Val']

	def destroy(this):
		if(this._eventListen != None):
			this._bpVarRef.off(this._eventListen, this._onChanged)

		BPVarGetSet.destroy(this)

@registerInterface('BPIC/BP/Var/Set')
class IVarSet(BPVarGetSet):
	def changeVar(this, name, scopeId):
		scope = BPVarGetSet.changeVar(this, name, scopeId)
		this.title = "Set name"

		temp = scope[this.data['name']]
		this._bpVarRef = temp
		if(temp.type == BPVarTemp.typeNotSet): return scope

		this._reinitPort()

	def _reinitPort(this):
		input = this.input
		node = this.node
		temp = this._bpVarRef

		if('Val' in input):
			node.deletePort('input', 'Val')

		if(temp.type == FunctionType):
			def call(port):
				temp.emit('call')

			node.createPort('input', 'Val', Port.Trigger(call))

		else: node.createPort('input', 'Val', temp.type)

		return input['Val']