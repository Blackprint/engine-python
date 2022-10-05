from types import FunctionType
from typing import Dict

from ..Internal import EvPortSelf
from ..Utils import Utils
from ..Port.PortFeature import Port
from ..Types import Types
from .Port import Port as PortClass
from collections.abc import MutableMapping

class PortLink(MutableMapping):
	_iface = None
	_which = None
	_ifacePort: Dict[str, PortClass] = None

	def __init__(this, node, which, portMeta):
		iface = node.iface
		this._iface = iface
		this._which = which

		link = {}
		this._ifacePort = link

		if(which == 'input'):
			iface.input = link
		else:
			iface.output = link

		# Create linker for all port
		for portName, val in portMeta.items():
			this._add(portName, val)

	def __getitem__(this, key):
		port = this._ifacePort[key]

		# This port must use values from connected output
		if(port.source == 'input'):
			if(port._cache != None): return port._cache

			cableLen = len(port.cables)
			if(cableLen == 0):
				return port.default

			# Flag current iface is requesting value to other iface
			port.iface._requesting = True

			# Return single data
			if(cableLen == 1):
				cable = port.cables[0] # Don't use pointer

				if(cable.connected == False or cable.disabled):
					port.iface._requesting = False
					if(port.feature == Port.ArrayOf):
						port._cache = []

					port._cache = port.default
					return port._cache

				output = cable.output

				# Request the data first
				if(output.value == None):
					output.iface.node.request(cable)

				# print(f"\n1. {port.name} . {output.name} ({output.value})")

				port.iface._requesting = False

				if(port.feature == Port.ArrayOf):
					port._cache = []

					if(output.value != None):
						port._cache.append(output.value)

					return port._cache

				finalVal = output.value
				if finalVal == None:
					finalVal = port.default

				port._cache = finalVal
				return port._cache

			isNotArrayPort = port.feature != Port.ArrayOf

			# Return multiple data as an array
			cables = port.cables
			data = []
			for cable in cables:
				if(cable.connected == False or cable.disabled):
					continue

				output = cable.output

				# Request the data first
				if(output.value == None):
					output.iface.node.request(cable)

				# print(f"\n2. {port.name} . {output.name} ({output.value})")

				finalVal = output.value
				if finalVal == None:
					finalVal = port.default

				if(isNotArrayPort):
					port.iface._requesting = False
					port._cache = finalVal
					return port._cache

				data.append(finalVal)

			port.iface._requesting = False

			port._cache = data
			return data
		# else: output ports

		# Callable port (for output ports)
		if(port._callAll != None):
			return port._callAll

		return port.value

	def __setitem__(this, key, val):
		port = this._ifacePort[key]

		if(port == None):
			raise Exception(f"Port {this._which} ('{key}') was not found on node with namespace '{this._iface.namespace}'")

		# setter (only for output port)
		if(port.iface.node.disablePorts or (not (port.splitted or port.allowResync) and port.value == val)):
			return

		if(port.source == 'input'):
			raise Exception("Can't set data to input port")

		if(val == None):
			val = port.default
		else:
			# Type check
			if port.type == Types.Any:
				pass
			elif isinstance(val, port.type):
				pass
			else: raise Exception(f"Can't validate type: {type(val).__name__} != {port.type.__name__}")

		# print(f"\n3. {port.iface.title}.{port.name} = {val}")

		port.value = val
		port.emit('value', EvPortSelf(port))

		if(port.feature == Port.StructOf and port.splitted):
			Port.StructOf_handle(port, val)
			return

		if(port._sync == False):
			return

		port.sync()

	def __delitem__(this, key):
		# dict.__delitem__(this, key)
		raise Exception("Can't delete port with 'del' command")

	def __iter__(this):
		return this._ifacePort.__iter__(this)

	def __len__(this):
		return this._ifacePort.__len__(this)

	def __contains__(this, x):
		return this._ifacePort.__contains__(this,x)

	def _add(this, portName, val):
		iPort = this._ifacePort

		if(portName in iPort):
			return iPort[portName]

		# Determine type and add default value for each type
		[ type, def_, haveFeature ] = Utils.determinePortType(val, this)

		linkedPort = this._iface._newPort(portName, type, def_, this._which, haveFeature)
		iPort[portName] = linkedPort

		if(not (haveFeature == Port.Trigger and this._which == 'input')):
			linkedPort.createLinker()

		return linkedPort # IFace Port

	def _delete(this, portName):
		iPort = this._ifacePort

		# Destroy cable first
		port = iPort[portName]
		port.disconnectAll()

		del iPort[portName]

	def __str__(this):
		iPort = this._ifacePort
		temp = {}

		for k in iPort:
			temp[k] = this.__getitem__(k)

		return str(temp)