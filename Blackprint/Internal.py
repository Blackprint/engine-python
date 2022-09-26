import re
import os
# from .Utils import Utils

class Internal:
	nodes = {}
	interface = {}
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
	# 			Utils.deepProperty(Internal.nodes, path.split('/'), temp)
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
	def __init__(this, scope, id):
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