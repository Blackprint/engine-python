import re
import os
from . import Interface, Utils
from importlib import import_module

class Internal:
	nodes = {}
	interface = {}
	namespace = []

	@staticmethod
	def _loadNamespace(path):
		namespace = Internal.namespace

		if(re.search('[<>:"\'|?*\\\\]', path) or (".." in path)):
			raise Exception(f"Illegal character detected [{path}] when importing nodes!")

		for value in namespace:
			temp = f"{value}/{path}.py"

			if(os.path.isfile(temp)):
				__import__(temp)
				temp = "BPNode/$path".replace('/', '\\')
				Utils.deepProperty(Internal.nodes, path.split('/'), temp)
				return

def registerNode(namespace: str): # Decorator
	namespace = namespace.replace('\\', '/')

	def register(clazz):
		Internal.nodes[namespace] = clazz
		return clazz

	return register

def registerInterface(templatePath: str): # Decorator
	templatePath = templatePath.replace('\\', '/')

	if(not templatePath.startswith('BPIC/')):
		raise Exception("$templatePath: The first parameter of 'registerInterface' must be started with BPIC to avoid name conflict. Please name the interface similar with 'templatePrefix' for your module that you have set on 'blackprint.config.js'.", 1)

	def register(clazz):
		Internal.interface[templatePath] = clazz
		return clazz

	return register

def registerNamespace(fullPath: str):
	if fullPath not in Internal.namespace:
		Internal.namespace.append(fullPath)

def _loadNode(path):
	for fullPath in Internal.namespace:
		temp = fullPath + path

		if os.path.isfile(temp):
			import_module(temp)

Internal.interface['BP/default'] = Interface

# Below is for internal only
# class EvIface:
# 	function __init__(
# 		iface
# 	):}

# class EvPort:
# 	function __init__(
# 		port
# 	):}

# class EvEnv:
# 	function __init__(
# 		key,
# 		value=None,
# 	):}

# class EvVariableNew:
# 	function __init__(
# 		scope,
# 		id,
# 	):}

# class EvPortValue:
# 	function __init__(
# 		port,
# 		target,
# 		cable,
# 	):}

# class EvPortSelf:
# 	function __init__(
# 		port
# 	):}