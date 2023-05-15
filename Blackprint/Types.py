class Any: _internal = True
class Slot: _internal = True
class Route: _internal = True

class Types:
	Any = Any
	Slot = Slot
	Route = Route

	@staticmethod
	def isType(type):
		if(type == Types.Any): return True
		if(type == Types.Slot): return True
		if(type == Types.Route): return True
		return False