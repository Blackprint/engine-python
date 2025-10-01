import asyncio
from .Types import Types
from .Port.PortFeature import Port

class Utils:
	NoOperation = lambda: None

	@staticmethod
	def setDeepProperty(obj, path, value=None, onCreate=None):
		if not path:
			return

		# Check each path component type
		for key in path[:-1]:
			if not isinstance(key, (str, int, float)):
				raise Exception(f"Object field must be Number or String, but found: {repr(key)}")

			# Disallow diving into internal Python property
			if key in ("__class__", "__dict__", "__weakref__", "__module__", "__bases__"):
				return

			if key not in obj:
				obj[key] = {}
				if onCreate:
					onCreate(obj[key])

			obj = obj[key]

		# Check the last path component type
		lastKey = path[-1]
		if not isinstance(lastKey, (str, int, float)):
			raise Exception(f"Object field must be Number or String, but found: {repr(lastKey)}")

		if lastKey in ("__class__", "__dict__", "__weakref__", "__module__", "__bases__"):
			return

		obj[lastKey] = value
		return

	@staticmethod
	def getDeepProperty(obj, path, reduceLen=0):
		if not path:
			return None

		n = len(path) - reduceLen
		if n <= 0:
			return None

		for i in range(n):
			key = path[i]
			if key not in obj:
				return None
			obj = obj[key]

		return obj

	@staticmethod
	def deleteDeepProperty(obj, path, deleteEmptyParent=False):
		if not path:
			return

		lastPath = path[-1]
		parents = []

		# Navigate to the parent of the target
		for key in path[:-1]:
			if key not in obj:
				return
			parents.append(obj)
			obj = obj[key]

		# Delete the target property
		if lastPath in obj:
			del obj[lastPath]

		# Clean up empty parents if requested
		if deleteEmptyParent:
			for i in range(len(parents)-1, -1, -1):
				parent = parents[i]
				key = path[i]
				if key not in parent:
					continue

				# Check if the object is empty
				if hasattr(parent[key], '__len__') and len(parent[key]) == 0:
					del parent[key]
				elif not hasattr(parent[key], '__len__'):
					# For non-container objects, assume they're "empty" if they have no attributes
					if not hasattr(parent[key], '__dict__') or not parent[key].__dict__:
						del parent[key]
				else:
					break  # Object is not empty, stop cleaning up

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
		if(corountine == None): return
		try:
			task = asyncio.create_task(corountine)
			Utils._asyncTask.add(task)
			task.add_done_callback(Utils._asyncTask.discard)
		except RuntimeError:
			# No event loop running, use asyncio.run() to create one
			asyncio.run(corountine)

	def patchClass(old_class, new_class):
		for name in list(vars(old_class).keys()):
			if not name.startswith("__"):
				delattr(old_class, name)

		for name, value in vars(new_class).items():
			if not name.startswith("__"):
				setattr(old_class, name, value)

	@staticmethod
	def _combineArray(A, B):
		list = []
		if A is not None:
			list.extend(A)
		if B is not None:
			list.extend(B)
		return list