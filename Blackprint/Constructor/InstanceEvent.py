import re
from ..Nodes.Enums import Enums
from .CustomEvent import CustomEvent
from ..Types import Types

class InstanceEvents(CustomEvent):
	list = {}
	def __init__(this, instance):
		CustomEvent.__init__(this)
		this.instance = instance

	# No need to override like engine-js as it's already performant
	# function emit(eventName, obj): }

	def createEvent(this, namespace, options={}):
		if(namespace in this.list): return
		if(re.search(r'/\s/', namespace) != None):
			raise Exception(f"Namespace can't have space character: '{namespace}'")

		schema = []
		if('schema' in options):
			list = options['schema']
			for value in list:
				schema[value] = Types.Any

		this.list[namespace] = InstanceEvent({ 'schema': schema })

	def _renameFields(this, namespace, name, to):
		schema = this.list[namespace]
		if(schema == None): return
		schema = schema.schema
		if(schema == None): return

		schema[to] = schema[name]
		del schema[name]

		this.refreshFields(namespace, name, to)

	# second and third parameter is only be used for renaming field
	def refreshFields(this, namespace, _name=None, _to=None):
		schema = this.list[namespace]
		if(schema == None): return
		schema = schema.schema
		if(schema == None): return

		def refreshPorts(iface, target):
			ports = iface[target]
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
				if(ports[target] == None):
					node.createPort(target, name, schema[name])

		def callback(ifaceList):
			for iface in ifaceList:
				if(iface._enum == Enums.BPEventListen):
					if(iface.data['namespace'] == namespace):
						refreshPorts(iface, 'output')

				elif(iface._enum == Enums.BPEventEmit):
					if(iface.data['namespace'] == namespace):
						refreshPorts(iface, 'input')

				elif(iface._enum == Enums.BPFnMain):
					iterateList(iface.bpInstance.ifaceList)

		iterateList = callback
		iterateList(this.instance.ifaceList)

class InstanceEvent:
	schema = None
	def __init__(this, options):
		this.schema = options['schema']