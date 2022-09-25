from .Constructor.References import References
from .Constructor.CustomEvent import CustomEvent
from .Constructor.PortLink import PortLink
from .Constructor.Port import Port as PortClass
from .RoutePort import RoutePort
from .Port.PortFeature import Port

from typing import TYPE_CHECKING
if TYPE_CHECKING:
	from .Node import Node

class Temp:
	list = ['input', 'output']

class Interface(CustomEvent):
	id: str # Named ID
	i: int # Generated Index
	title = 'No title'
	interface = 'BP/default'
	importing = True
	_dynamicPort = False
	_enum = None
	isGhost = False

	node: 'Node'
	namespace: str
	_requesting = False

	# @var Nodes/FnMain 
	_funcMain = None

	ref: References

	def __init__(this, node):
		this.node = node

	def _prepare_(this, clazz):
		node = this.node
		ref = References()
		node.ref = ref
		this.ref = ref

		node.routes = RoutePort(this)

		if(clazz.output != None):
			node._outputLink = PortLink(node, 'output', clazz.output)
			ref.IOutput = this.output
			ref.Output = node.output

		if(clazz.Input != None):
			node._inputLink = PortLink(node, 'input', clazz.input)
			ref.IInput = this.input
			ref.Input = node.input

		if(clazz.property):
			raise Exception("'node.property', 'iface.property', and 'static \$property' is reserved field for Blackprint")

	def _newPort(this, portName, type, def_, which, haveFeature):
		return PortClass(portName, type, def_, which, this, haveFeature)

	def _initPortSwitches(this, portSwitches):
		for key, value in portSwitches.items():
			ref = this.output[key]

			if((value | 1) == 1):
				Port.StructOf_split(ref)

			if((value | 2) == 2):
				ref.allowResync = True

	def _importInputs(this, ports):
		# Load saved port data value
		inputs = this.input
		for key, val in ports.items():
			if(inputs.has_key(key)):
				port = inputs[key]
				port.default = val

	def _BpFnInit(this):
		pass

	def init(this):
		pass
	def destroy(this):
		pass
	def imported(this, data):
		pass