class Types:
	Any = object()
	Slot = object()
	Route = object()

	@staticmethod
	def isType(type):
		if(type == Types.Any): return True
		if(type == Types.Slot): return True
		if(type == Types.Route): return True
		return False