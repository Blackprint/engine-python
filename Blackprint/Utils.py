from .Types import Types
from .Port.PortFeature import Port

class Utils:
	NoOperation = lambda: None

	@staticmethod
	def deepProperty(obj, path, value = None):
		if(value != None):
			last = path.pop()
			for key in path:
				if(obj.has_key(key) == False):
					obj[key] = []

				obj = obj[key]

			obj[last] = value
			return

		for key in path:
			obj = obj[key]

			if(obj == None):
				return obj

		return obj

	@staticmethod
	def determinePortType(val, that):
		if(val == None):
			raise Exception(f"Port type can't be None, error when processing: {that._iface.title}, {that._which} port")
	
		type = val
		def_ = None
		feature = val['feature']
	
		if(feature == Port.Trigger):
			def_ = val['func']
			type = Types.Function

		elif(feature == Port.ArrayOf):
			type = val['type']

			if(type == Types.Any):
				def_ = None
			else: def_ = []

		elif(feature == Port.Union):
			type = val['type']
		elif(feature == Port.Default):
			type = val['type']
			def_ = val['value']

		# Give default value for each primitive type
		elif(type == Types.Number):
			def_ = 0
		elif(type == Types.Boolean):
			def_ = False
		elif(type == Types.String):
			def_ = ''
		elif(type == Types.Array):
			def_ = []
		elif(type == Types.Any): 0 # Any
		elif(type == Types.Function): 0
		elif(type == Types.Route): 0
		elif(feature == None):
			raise Exception("Port for initialization must be a types", 1)
		# else{
		# 	def = port
		# 	type = Types.String
		# }
	
		return [ type, def_, feature ]