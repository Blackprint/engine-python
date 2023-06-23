from ..Types import Types
from typing import Dict

from ..Port.PortFeature import Port
from ..Utils import Utils
from ..Interface import Interface
from ..Node import Node
from ..Environment import Environment
from .Enums import Enums
from ..Internal import registerNode, registerInterface

@registerNode('BP/Event/Listen')
class BPEventListen(Node):
	# Defined below this class
	input = {
		"Limit": Port.Default(int, 0),
		"Reset": Port.Trigger(lambda port: port.iface.node.resetLimit()),
		"Off": Port.Trigger(lambda port: port.iface.node.offEvent()),
	}
	output = {}

	# @var IEventListen 
	iface = None
	_limit = -1 # -1 = no limit
	_off = False

	def __init__(this, instance):
		Node.__init__(this, instance)
		iface = this.setInterface('BPIC/BP/Event/Listen')

		# Specify data field from here to make it enumerable and exportable
		iface.data = {"namespace": ''}
		iface.title = 'EventListen'
		# iface.type = 'event'

		iface._enum = Enums.BPEventListen

	def initPorts(this, data): this.iface.initPorts(data)
	def resetLimit(this):
		limit = this.input['Limit']
		this._limit = -1 if limit == 0 else limit

		if(this._off):
			iface = this.iface
			this.instance.events.on(iface.data['namespace'], iface._listener)

	def eventUpdate(this, obj):
		if(this._off or this._limit == 0): return
		if(this._limit > 0): this._limit -= 1

		# Don't use object assign as we need to re-assign None/undefined field
		output = this.iface.output
		for key, port in output.items():
			port.value = obj[key]
			port.sync()

		this.routes.routeOut()

	def offEvent(this):
		if(this._off == False):
			iface = this.iface
			this.instance.events.off(iface.data['namespace'], iface._listener)

			this._off = True

	def destroy(this):
		iface = this.iface

		if(iface._listener == None): return
		iface._insEventsRef.off(iface.data['namespace'], iface._listener)

@registerNode('BP/Event/Emit')
class BPEventEmit(Node):
	# Defined below this class
	input = {
		"Emit": Port.Trigger(lambda port: port.iface.node.trigger()),
	}

	# @var IEnvEmit 
	iface = None

	def __init__(this, instance):
		Node.__init__(this, instance)
		iface = this.setInterface('BPIC/BP/Event/Emit')

		# Specify data field from here to make it enumerable and exportable
		iface.data = {"namespace": ''}
		iface.title = 'EventEmit'
		# iface.type = 'event'

		iface._enum = Enums.BPEventEmit

	def initPorts(this, data): this.iface.initPorts(data)
	def trigger(this):
		data = {} # Copy data from input ports
		IInput = this.iface.input
		Input = this.input

		for key, value in IInput.items():
			if(key == 'Emit'): continue
			data[key] = Input[key] # Obtain data by triggering the offsetGet (getter)

		this.instance.events.emit(this.iface.data['namespace'], data)

class BPEventListenEmit(Interface):
	# _nameListener
	_insEventsRef = None
	_eventRef = None
	def __init__(this, node):
		Interface.__init__(this, node)
		this._insEventsRef = this.node.instance.events

	def initPorts(this, data):
		namespace = data['namespace']
		if(not namespace): raise Exception("Parameter 'namespace' is required")

		this.data['namespace'] = namespace
		this.title = namespace

		this._eventRef = this.node.instance.events.list[namespace]
		if(this._eventRef == None): raise Exception("Events (namespace) is not defined")

		schema = this._eventRef.schema
		if(this._enum == Enums.BPEventListen):
			createPortTarget = 'output'

		else: createPortTarget = 'input'

		for key in schema:
			this.node.createPort(createPortTarget, key, Types.Any)

	def createField(this, name, type=Types.Any):
		schema = this._eventRef.schema
		if(schema[name] != None): return

		schema[name] = type
		this._insEventsRef.refreshFields(this.data['namespace'])
		this.node.instance.emit('eventfield.create', EvEFCreate(
			name,
			this.data['namespace']
		))

	def renameField(this, name, to):
		schema = this._eventRef.schema
		if(schema[name] == None or schema[to] != None): return

		this._insEventsRef._renameFields(this.data['namespace'], name, to)
		this.node.instance.emit('eventfield.rename', EvEFRename(
			name,
			to,
			this.data['namespace']
		))

	def deleteField(this, name, type=Types.Any):
		schema = this._eventRef.schema
		if(schema[name] != None): return

		del schema[name]
		this._insEventsRef.refreshFields(this.data['namespace'])
		this.node.instance.emit('eventfield.delete', EvEFDelete(
			name,
			this.data['namespace']
		))

@registerInterface('BPIC/BP/Event/Listen')
class IEventListen(BPEventListenEmit):
	_listener = None
	# @var BPEventListen 
	node = None
	def initPorts(this, data):
		BPEventListenEmit.initPorts(this, data)

		if(this._listener): raise Exception("This node already listen to an event")
		this._listener = lambda ev: this.node.eventUpdate(ev)

		this._insEventsRef.on(data['namespace'], this._listener)


@registerInterface('BPIC/BP/Event/Emit')
class IEnvEmit(BPEventListenEmit):
	pass

class EvEFCreate:
	def __init__(this, name, namespace):
		this.name = name
		this.namespace = namespace

class EvEFRename:
	def __init__(this, name, to, namespace):
		this.name = name
		this.to = to
		this.namespace = namespace

class EvEFDelete:
	def __init__(this, name, namespace):
		this.name = name
		this.namespace = namespace