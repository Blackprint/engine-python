from Constructor import CustomEvent
from Constructor import Node
from importlib import import_module
import os

class Engine(CustomEvent.CustomEvent):
	iface = []
	ifaceList = []
	_settings = []
	disablePorts = False
	throwOnError = True

	variables = []
	functions = []
	ref = []

	def __init__(self):
		pass

	def importJSON(this, json, options=None):
		pass


_nodes = {}
def registerNode(name: str): # Decorator
	def register(clazz):
		global _nodes
		print("Node registered: "+name)

		_nodes[name] = clazz
		return clazz

	return register

_iface = {}
def registerInterface(name: str): # Decorator
	def register(clazz):
		global _iface

		_iface[name] = clazz
		return clazz

	return register

namespaces = []
def registerNamespace(fullPath: str):
	global namespaces

	if fullPath not in namespaces:
		namespaces.append(fullPath)

def _loadNode(path):
	for fullPath in namespaces:
		temp = fullPath + path

		if os.path.isfile(temp):
			import_module(temp)