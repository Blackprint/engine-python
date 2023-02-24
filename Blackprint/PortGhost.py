from .Interface import Interface
from .Node import Node
from .Utils import Utils
from .Constructor.Port import Port

class PortGhost(Port):
	fakeIface = None
	def destroy(this):
		this.disconnectAll(False)

class fakeInstance:
	def emit(this, a, b):
		pass

class fakeNode:
	instance = fakeInstance()

class fakeIface:
	title = "Blackprint.PortGhost"
	isGhost = True
	node = None
	emit = None
	_iface = None
	input = {}
	output = {}
	def __init__(this):
		this.node = fakeNode()
	def emit(this, a, b):
		pass

_fakeIface = fakeIface()
_fakeIface._iface = _fakeIface

# These may be useful for testing or creating custom port without creating nodes when scripting
class OutputPort(PortGhost):
	_ghost = True
	def __init__(this, type):
		( type, def_, haveFeature ) = Utils.determinePortType(type, _fakeIface)

		PortGhost.__init__(this, 'Blackprint.OutputPort', type, def_, 'output', _fakeIface, haveFeature)

class InputPort(PortGhost):
	_ghost = True
	def __init__(this, type):
		( type, def_, haveFeature ) = Utils.determinePortType(type, _fakeIface)

		PortGhost.__init__(this, 'Blackprint.InputPort', type, def_, 'input', _fakeIface, haveFeature)