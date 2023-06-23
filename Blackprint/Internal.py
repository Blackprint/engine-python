import re
# from .Utils import Utils
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
		Internal.nodes[namespace] = clazz
		return clazz

	return register

def registerInterface(templatePath: str): # Decorator
	templatePath = templatePath.replace('\\', '/')

	if(not templatePath.startswith('BPIC/')):
		raise Exception(f"{templatePath}: The first parameter of 'registerInterface' must be started with BPIC to avoid name conflict. Please name the interface similar with 'templatePrefix' for your module that you have set on 'blackprint.config.js'.", 1)

	def register(clazz):
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

	for obj in schema:
		# Must be a data type
		# or type from Blackprint.Port.{Feature}
		if(not isinstance(obj, type) and obj.feature == None) and not Types.isType(obj):
			raise Exception(f"Unsupported schema type for field 'key' in '{namespace}'")
	
	Internal.events[namespace] = InstanceEvent(options)

def createVariable(namespace, options=[]):
	if(re.search(r'/\s/', namespace) != None):
		raise Exception(f"Namespace can't have space character: '{namespace}'")

	temp = BPVariable(namespace, options)
	temp._scope = VarScope.public
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

class EvVariableNew:
	def __init__(this, instance, scope, id):
		this.instance = instance
		this.scope = scope
		this.id = id

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