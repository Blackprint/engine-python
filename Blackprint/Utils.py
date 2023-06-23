import asyncio
from .Types import Types
from .Port.PortFeature import Port

class Utils:
	NoOperation = lambda: None

	@staticmethod
	def setDeepProperty(obj, path, value = None):
		last = path.pop()
		for key in path:
			if(key not in obj):
				obj[key] = {}

			obj = obj[key]

		obj[last] = value
		return

	@staticmethod
	def getDeepProperty(obj, path, reduceLen = 0):
		i = len(path) - reduceLen
		for key in path:
			if(key not in obj):
				return None

			obj = obj[key]

			i -= 1
			if(i == 0): break

		return obj

	@staticmethod
	def determinePortType(val, that):
		if(val == None):
			raise Exception(f"Port type can't be None, error when processing: {that._iface.namespace}, {that._which} port")
	
		type = val
		def_ = None
		feature = None
	
		if(isinstance(val, dict)):
			feature = val['feature']
			if(feature == Port.Trigger):
				def_ = val['func']
				type = val['type']

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
		elif(type == int or type == float):
			def_ = 0
		elif(type == bool):
			def_ = False
		elif(type == str):
			def_ = ''
		elif(type == list):
			def_ = []
		# elif(type == Types.Trigger): 0
		# elif(type == Types.Any): 0 # Any
		# elif(type == Types.Slot): 0
		# elif(type == Types.Route): 0
		# elif(feature == None):
		# 	print(type)
		# 	raise Exception("Unrecognized port type or port feature", 1)
		# else{
		# 	def = port
		# 	type = str
		# }
	
		return ( type, def_, feature )
	
	def findFromList(list, item):
		try:
			return list.index(item)
		except ValueError:
			return None

	_asyncTask = set()
	def runAsync(corountine):
		return

		task = asyncio.create_task(corountine)
		Utils._asyncTask.add(task)
		task.add_done_callback(Utils._asyncTask.discard)
