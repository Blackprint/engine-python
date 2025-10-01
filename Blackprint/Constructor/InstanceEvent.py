import re
from ..Nodes.Enums import Enums
from .CustomEvent import CustomEvent
from ..Types import Types

class InstanceEvents(CustomEvent):
	list = {}
	def __init__(this, instance):
		CustomEvent.__init__(this)
		this.instance = instance

	def createEvent(this, namespace, options={}):
		if(namespace in this.list): return # throw new Error(f"Event with name '{namespace}' already exist")
		if(re.search(r'/\s/', namespace) != None):
			raise Exception(f"Namespace can't have space character: '{namespace}'")

		if('schema' in options and isinstance(options['schema'], list)):
			options['fields'] = options['schema']
			del options['schema']
			print(".createEvent: schema options need to be object, please re-export this instance and replace your old JSON")

		schema = options.get('schema', {})
		list_ = options.get('fields', None)
		if(list_ != None):
			for value in list_:
				schema[value] = Types.Any

		obj = this.list[namespace] = InstanceEvent({ 'schema': schema, 'namespace': namespace, '_root': this })

		this.instance._emit('event.created', {'reference': obj})

	def renameEvent(this, from_, to):
		if(to in this.list): raise Exception(f"Event with name '{to}' already exist")
		if(re.search(r'/\s/', to) != None):
			raise Exception(f"Namespace can't have space character: '{to}'")

		oldEvInstance = this.list[from_]
		used = oldEvInstance.used
		oldEvInstance.namespace = to

		for iface in used:
			if(iface._enum == Enums.BPEventListen):
				this.off(iface.data['namespace'], iface._listener)
				this.on(to, iface._listener)

			iface.data['namespace'] = to
			iface.title = ' '.join(to.split('/')[-2:])

		this.list[to] = this.list[from_]
		del this.list[from_]

		this.instance._emit('event.renamed', {'old': from_, 'now': to, 'reference': oldEvInstance})

	def deleteEvent(this, namespace):
		exist = this.list.get(namespace, None)
		if(exist == None): return

		map = exist.used # This list can be altered multiple times when deleting a node
		for iface in reversed(map):
			iface.node.instance.deleteNode(iface)

		del this.list[namespace]
		this.instance._emit('event.deleted', {'reference': exist})

	def _renameFields(this, namespace, name, to):
		schema = this.list.get(namespace, None)
		if(schema == None): return
		schema = schema.schema
		if(schema == None): return

		schema[to] = schema[name]
		del schema[name]

		this.refreshFields(namespace, name, to)

	# second and third parameter is only be used for renaming field
	def refreshFields(this, namespace, _name=None, _to=None):
		evInstance = this.list.get(namespace, None)
		schema = evInstance.schema if evInstance else None
		if(schema == None): return

		def refreshPorts(iface, target):
			ports = getattr(iface, target)
			node = iface.node

			if(_name != None):
				node.renamePort(target, _name, _to)
				return

			# Delete port that not exist or different type first
			isEmitPort = True if target == 'input' else False
			for name, val in ports.items():
				if(isEmitPort):
					isEmitPort = False
					continue
				if(schema[name] != ports[name]._config):
					node.deletePort(target, name)

			# Create port that not exist
			for name, val in schema.items():
				if(ports.get(target, None) == None):
					node.createPort(target, name, schema[name])

		used = evInstance.used
		for iface in used:
			if(iface._enum == Enums.BPEventListen):
				if(iface.data['namespace'] == namespace):
					refreshPorts(iface, 'output')
			elif(iface._enum == Enums.BPEventEmit):
				if(iface.data['namespace'] == namespace):
					refreshPorts(iface, 'input')
			else: raise Exception("Unrecognized node in event list's stored nodes")

class InstanceEvent:
	schema = None
	def __init__(this, options):
		this.schema = options['schema']
		this._root = options.get('_root', None)
		this.namespace = options.get('namespace', None)
		this.used = []