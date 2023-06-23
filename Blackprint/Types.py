class Any: _internal = True
class Slot: _internal = True
class Route: _internal = True
class Trigger: _internal = True

class Types:
	Any = Any
	Slot = Slot
	Route = Route
	Trigger = Trigger

	@staticmethod
	def isType(type):
		if(type == Types.Any): return True
		if(type == Types.Slot): return True
		if(type == Types.Route): return True
		if(type == Types.Trigger): return True
		return False