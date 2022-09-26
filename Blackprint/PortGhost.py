from .Interface import Interface
from .Node import Node
from .Utils import Utils
from .Constructor.Port import PortClass

class PortGhost(PortClass):
	fakeIface = None
	def destroy(this):
		this.disconnectAll(False)

fakeIface = Interface()
fakeIface.title = "Blackprint.PortGhost"
fakeIface.isGhost = True
fakeIface.node = Node()

fakeIface._iface = fakeIface
PortGhost.fakeIface = fakeIface

# These may be useful for testing or creating custom port without creating nodes when scripting
class OutputPort(PortGhost):
	_ghost = True
	def __init__(this, type):
		( type, def_, haveFeature ) = Utils.determinePortType(type, PortGhost.fakeIface)

		PortGhost.__init__(this, 'Blackprint.OutputPort', type, def_, 'output', fakeIface, haveFeature)

class InputPort(PortGhost):
	_ghost = True
	def __init__(this, type):
		( type, def_, haveFeature ) = Utils.determinePortType(type, PortGhost.fakeIface)

		PortGhost.__init__(this, 'Blackprint.InputPort', type, def_, 'input', fakeIface, haveFeature)