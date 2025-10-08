import re
from .Utils import Utils
from .Constructor import InstanceEvent
from .Types import Types
from .Nodes.BPVariable_init import BPVariable, VarScope

class Internal:
	nodes = {}
	interface = {}
	events = {}
	# namespace = []

	# @staticmethod
	# def _loadNamespace(path):
	# 	namespace = Internal.namespace

	# 	if(re.search(r'[<>:"\'|?*\\\\]', path) or (".." in path)):
	# 		raise Exception(f"Illegal character detected [{path}] when importing nodes!")

	# 	for value in namespace:
	# 		temp = f"{value}/{path}.py"

	# 		if(os.path.isfile(temp)):
	# 			path_import(value, path)
	# 			temp = "BPNode/$path".replace('/', '\\')
	# 			Utils.setDeepProperty(Internal.nodes, path.split('/'), temp)
	# 			return

def registerNode(namespace: str): # Decorator
	namespace = namespace.replace('\\', '/')

	def register(clazz):
		if(namespace in Internal.nodes):
			Utils.patchClass(Internal.nodes[namespace], clazz)
			return Internal.nodes[namespace]

		Internal.nodes[namespace] = clazz
		return clazz

	return register

def registerInterface(templatePath: str): # Decorator
	templatePath = templatePath.replace('\\', '/')

	if(not templatePath.startswith('BPIC/')):
		raise Exception(f"{templatePath}: The first parameter of 'registerInterface' must be started with BPIC to avoid name conflict. Please name the interface similar with 'templatePrefix' for your module that you have set on 'blackprint.config.js'.", 1)

	def register(clazz):
		if(templatePath in Internal.interface):
			Utils.patchClass(Internal.interface[templatePath], clazz)
			return Internal.interface[templatePath]

		Internal.interface[templatePath] = clazz
		return clazz

	return register

# def registerNamespace(fullPath: str):
# 	if fullPath not in Internal.namespace:
# 		Internal.namespace.append(fullPath)

def registerEvent(namespace, options):
	if(re.search(r'/\s/', namespace) != None):
		raise Exception(f"Namespace can't have space character: '{namespace}'")

	schema = options['schema']
	if(schema == None):
		raise Exception(f"Registering an event must have a schema. If the event doesn't have a schema or dynamically created from an instance you may not need to do this registration.")

	for key, obj in schema.items():
		# Must be a data type
		# or type from Blackprint.Port.{Feature}
		if(not isinstance(obj, type) and obj.feature == None) and not Types.isType(obj):
			raise Exception(f"Unsupported schema type for field '{key}' in '{namespace}'")

	Internal.events[namespace] = InstanceEvent(options)

def createVariable(namespace, options=[]):
	if(re.search(r'/\s/', namespace) != None):
		raise Exception(f"Namespace can't have space character: '{namespace}'")

	temp = BPVariable(namespace, options)
	temp._scope = VarScope.Public
	temp.isShared = True

	return temp

# Below is for internal only
class EvError:
	def __init__(this, type, data):
		this.type = type
		this.data = data

class EvIface:
	def __init__(this, iface):
		this.iface = iface

class EvPort:
	def __init__(this, port):
		this.port = port

class EvEnv:
	def __init__(this, key, value=None):
		this.key = key
		this.value = value

class EvCable:
	def __init__(this, cable):
		this.cable = cable

class EvPortValue:
	def __init__(this, port, target, cable):
		this.port = port
		this.target = target
		this.cable = cable

class EvPortSelf:
	def __init__(this, port):
		this.port = port

class EvCableError:
	def __init__(this, iface, port, target, msg):
		this.iface = iface
		this.port = port
		this.target = target
		this.message = msg

class EvJsonImporting:
	def __init__(this, append_mode, data):
		this.appendMode = append_mode
		this.data = data

class EvJsonImported:
	def __init__(this, append_mode, start_index, nodes, data):
		this.appendMode = append_mode
		this.startIndex = start_index
		this.nodes = nodes
		this.data = data

class EvVariableNew:
	def __init__(this, scope, id, bpFunction, reference):
		this.scope = scope
		this.id = id
		this.bpFunction = bpFunction
		this.reference = reference # Only available for Public/Shared scope

class EvVariableRenamed:
	def __init__(this, scope, old_name, new_name, bp_function, reference):
		this.scope = scope
		this.old = old_name
		this.now = new_name
		this.bpFunction = bp_function
		this.reference = reference # Only available for Public/Shared scope

class EvVariableDeleted:
	def __init__(this, scope, id, bp_function):
		this.scope = scope
		this.id = id
		this.bpFunction = bp_function

class EvFunctionNew:
	def __init__(this, reference):
		this.reference = reference

class EvFunctionRenamed:
	def __init__(this, old_name, new_name, reference):
		this.old = old_name
		this.now = new_name
		this.reference = reference

class EvFunctionDeleted:
	def __init__(this, id, reference):
		this.id = id
		this.reference = reference

class EvExecutionTerminated:
	def __init__(this, reason, iface):
		this.reason = reason
		this.iface = iface

class EvFieldCreated:
	def __init__(this, name, namespace):
		this.name = name
		this.namespace = namespace

class EvFieldRenamed:
	def __init__(this, old_name, new_name, namespace):
		this.old = old_name
		this.now = new_name
		this.namespace = namespace

class EvFieldDeleted:
	def __init__(this, name, namespace):
		this.name = name
		this.namespace = namespace

class EvEnvRenamed:
	def __init__(this, old_key, new_key):
		this.old = old_key
		this.now = new_key

class EvFunctionPortRenamed:
	def __init__(this, old_name, new_name, reference, which):
		this.old = old_name
		this.now = new_name
		this.reference = reference
		this.which = which

class EvFunctionPortDeleted:
	def __init__(this, which, name, reference):
		this.which = which
		this.name = name
		this.reference = reference

class EvNodeIdChanged:
	def __init__(this, iface, old_id, new_id):
		this.iface = iface
		this.old = old_id
		this.now = new_id

class EvNodeCreating:
	def __init__(this, namespace, options):
		this.namespace = namespace
		this.options = options

class EvNodeCreated:
	def __init__(this, iface):
		this.iface = iface