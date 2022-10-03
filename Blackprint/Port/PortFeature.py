from ..Types import Types

class Port:
	# This port can contain multiple cable as input
	# and the value will be array of 'type'
	# it's only one type, not union
	# for union port, please split it to different port to handle it

	@staticmethod
	def ArrayOf(type):
		return {
			'feature': Port.ArrayOf,
			'type': type
		}

	@staticmethod
	def ArrayOf_validate(type, target):
		if(type == Types.Any or target == Types.Any or type == target):
			return True

		if(isinstance(type, list) and (target in type)):
			return True

		return False

	# This port can have default value if no cable was connected
	# type = Type Data that allowed for the Port
	# value = default value for the port
	 
	@staticmethod
	def Default(type, val):
		return {
			'feature': Port.Default,
			'type': type,
			'value': val
		}

	# This port will be used as a trigger or callable input port
	# func = callback when the port was being called as a function
	 
	@staticmethod
	def Trigger(func):
		if func == None: raise Exception("Callback must not be None")
		return {
			'feature': Port.Trigger,
			'func': func
		}

	# This port can allow multiple different types
	# like an 'any' port, but can only contain one value
	 
	@staticmethod
	def Union(types):
		return {
			'feature': Port.Union,
			'type': types
		}

	@staticmethod
	def Union_validate(types, target):
		if(isinstance(types, list) and isinstance(target, list)):
			if(len(types) != len(target)): return False
	
			for type in types:
				if(type not in target):
					return False

	
			return True

	
		return (target == Types.Any) or (target in types)

	# This port can allow multiple different types
	# like an 'any' port, but can only contain one value
	 
	@staticmethod
	def StructOf(type, struct):
		return {
			'feature': Port.StructOf,
			'type': type,
			'value': struct
		}

	# VirtualType is only for browser with Sketch library
	def VirtualType():
		raise Exception("VirtualType is only for browser with Sketch library")
	
	@staticmethod
	def StructOf_split(port):
		if(port.source == 'input'):
			raise Exception("Port with feature 'StructOf' only supported for output port")

		node = port.iface.node
		struct = port.struct
		
		if port.structList == None:
			port.structList = port.struct.keys()

		for key, val in struct.items():
			if val._name == None:
				val._name = port.name.key

			newPort = node.createPort('output', val._name, val.type)
			newPort._parent = port
			newPort._structSplitted = True

		port.splitted = True
		port.disconnectAll()

		data = node.output[port.name]
		if(data != None): Port.StructOf_handle(port, data)

	@staticmethod
	def StructOf_unsplit(port):
		parent = port._parent
		if(parent == None and port.struct != None):
			parent = port

		parent.splitted = False

		struct = parent.struct
		node = port.iface.node

		for val in struct:
			node.deletePort('output', val._name)

	@staticmethod
	def StructOf_handle(port, data):
		struct = port.struct
		output = port.iface.node.output

		structList = port.structList
		if(data != None):
			for val in structList:
				ref = struct[val]
	
				if(ref.field != None):
					output[ref._name] = data[ref.field]
				else:
					output[ref._name] = ref.handle(data)

		else:
			for val in structList:
				output[struct[val]._name] = None