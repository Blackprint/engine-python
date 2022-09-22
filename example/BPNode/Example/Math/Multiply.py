from ..... import Blackprint
from .... import utils

@Blackprint.registerNode('Example/Math/Multiply')
class Multiply(Blackprint.Node):
	# Define input port here
	input = {
		'Exec': Blackprint.Port.Trigger,
		'A': Blackprint.Types.Number,
		'B': Blackprint.Types.Any,
	}

	# Define output port here
	output = {
		'Result': Blackprint.Types.Number,
	}

	def __init__(this, instance):
		super(Multiply, this).__init__(instance)

		iface = this.setInterface() # default interface
		iface.title = "Multiply"

	def init(this):
		iface = this.iface

		def onCableConnect(ev):
			utils.colorLog("Math/Multiply:", "Cable connected from {$ev.port.iface.title} ({$ev.port.name}) to {$ev.target.iface.title} ({$ev.target.name})")

		iface.on('cable.connect', onCableConnect) 

	# When any output value from other node are updated
	# Let's immediately change current node result
	def update(this, cable):
		this.output['Result'](this.multiply())

	# Your own processing mechanism
	def multiply(this):
		input = this.input

		utils.colorLog("Math/Multiply:", "Multiplying {$input['A']} with {$input['B']}")
		return input['A'] * input['B']

def Exec(port):
	node = port.iface.node

	node.output['Result'](node.multiply())
	utils.colorLog("Math/Multiply:", "Result has been set: "+node.output['Result'])

Multiply.input['Exec'] = Blackprint.Port.Trigger(Exec)