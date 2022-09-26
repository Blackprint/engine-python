import Blackprint
from ...utils import colorLog

def Exec(port):
	node = port.iface.node

	node.output['Result'] = node.multiply()
	colorLog("Math/Multiply:", f"Result has been set: {node.output['Result']}")

@Blackprint.registerNode('Example/Math/Multiply')
class Multiply(Blackprint.Node):
	# Define input port here
	input = {
		'Exec': Blackprint.Port.Trigger(Exec),
		'A': int,
		'B': Blackprint.Types.Any,
	}

	# Define output port here
	output = {
		'Result': int,
	}

	def __init__(this, instance):
		super(Multiply, this).__init__(instance)

		iface = this.setInterface() # default interface
		iface.title = "Multiply"

	def init(this):
		iface = this.iface

		def onCableConnect(ev):
			colorLog("Math/Multiply:", f"Cable connected from {ev.port.iface.title} ({ev.port.name}) to {ev.target.iface.title} ({ev.target.name})")

		iface.on('cable.connect', onCableConnect) 

	# When any output value from other node are updated
	# Let's immediately change current node result
	def update(this, cable):
		this.output['Result'] = this.multiply()

	# Your own processing mechanism
	def multiply(this):
		input = this.input

		colorLog("Math/Multiply:", f"Multiplying {input['A']} with {input['B']}")
		if input['B'] == None:
			return 55555

		return input['A'] * input['B']