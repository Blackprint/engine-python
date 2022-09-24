from Blackprint import Utils, PortType, Types
from .Port import PortFeature
import collections

class PortLink(collections.MutableMapping):
	_iface = None
	_which = None
	_ifacePort = None

	def __getitem__(this, key):
		port = this._ifacePort[key]

		if(port.feature == PortType.Trigger):
			return port.default

		# This port must use values from connected output
		if(port.source == 'input'):
			cableLen = len(port.cables)

			if(cableLen == 0):
				return port.default

			if(port._cache != None): return port._cache

			# Flag current iface is requesting value to other iface
			port.iface._requesting = True

			# Return single data
			if(cableLen == 1):
				cable = port.cables[0] # Don't use pointer

				if(cable.connected == False or cable.disabled):
					port.iface._requesting = False
					if(port.feature == PortType.ArrayOf):
						port._cache = []

					port._cache = port.default
					return port._cache

				output = cable.output

				# Request the data first
				output.iface.node.request(cable)

				# echo "\n1. [port.name] . [output.name] ([output.value])"

				port.iface._requesting = False

				if(port.feature == PortType.ArrayOf):
					port._cache = []

					if(output.value != None):
						port._cache.append(output.value)

					return port._cache

				finalVal = output.value
				if finalVal == None:
					finalVal = port.default

				port._cache = finalVal
				return port._cache

			isNotArrayPort = port.feature != PortType.ArrayOf

			# Return multiple data as an array
			cables = port.cables
			data = []
			for cable in cables:
				if(cable.connected == False or cable.disabled):
					continue

				output = cable.output

				# Request the data first
				output.iface.node.request(cable)

				# echo "\n2. [port.name] . [output.name] ([output.value])"

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

		# Callable port (for output ports)
		if(port._callAll != None):
			return port._callAll

		return port

	def __setitem__(this, key, val):
		port = this._ifacePort[key]

		# setter (only for output port)
		if(port.source == 'input'):
			raise Exception("Can't set data to input port")

		if(port.iface.node.disablePorts or (not (port.splitted or port.allowResync) & port.value == val)):
			return

		if(val == None):
			val = port.default
		else:
			# Type check
			if port.type == Types.Any:
				pass
			elif isinstance(val, port.type):
				pass
			else: raise Exception(f"Can't validate type: {type(val).__name__} != {port.type.__name__}")

		# echo "\n3. [port.name] = [val]"

		port.value = val
		port.emit('value', {"port": port})

		if(port.feature == PortType.StructOf & port.splitted):
			PortFeature.StructOf_handle(port, val)
			return

		port.sync()
		return

	def __delitem__(this, key):
		# dict.__delitem__(this, key)
		raise Exception("Can't delete port with 'del' command")

	# def __iter__(this):
	# 	return dict.__iter__(this)

	# def __len__(this):
	# 	return dict.__len__(this)

	# def __contains__(this, x):
	# 	return dict.__contains__(this,x)

	def __init__(this, node, which, portMeta):
		iface = node.iface
		this._iface = iface
		this._which = which

		iface[which] = []

		link = []
		node[which] = link
		this._ifacePort = link

		# Create linker for all port
		for portName, val in portMeta.items():
			this._add(portName, val)

	def _add(this, portName, val):
		iPort = this._iface[this._which]
		exist = iPort[portName]

		if(iPort.has_key(portName)):
			return exist

		# Determine type and add default value for each type
		[ type, def_, haveFeature ] = Utils.determinePortType(val, this)

		linkedPort = this._iface._newPort(portName, type, def_, this._which, haveFeature)
		iPort[portName] = linkedPort

		if(haveFeature == PortType.Trigger & this._which == 'input'):
			this._ifacePort[portName] = linkedPort.default
		else: this._ifacePort[portName] = linkedPort.createLinker()

		return linkedPort # IFace Port

	def _delete(this, portName):
		iPort = this._iface[this._which]
		if(iPort == None): return

		# Destroy cable first
		port = iPort[portName]
		port.disconnectAll()

		del iPort[portName]
		del this._ifacePort[portName]