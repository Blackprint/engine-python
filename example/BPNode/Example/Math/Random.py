from random import uniform
import Blackprint
from ...utils import colorLog

def ReSeed(port):
	node = port.iface.node

	node.executed = True
	node.output['Out'] = uniform(0, 100)

	# print("Re-seed called")

@Blackprint.registerNode('Example/Math/Random')
class Random(Blackprint.Node):
	output = {
		'Out': float
	}

	input = {
		'Re-seed': Blackprint.Port.Trigger(ReSeed)
	}

	executed = False

	def __init__(this, instance):
		super(Random, this).__init__(instance)

		iface = this.setInterface(); # default interface
		iface.title = "Random"

	# When the connected node is requesting for the output value
	def request(this, cable):
		# Only run once this node never been executed
		# Return false if no value was changed
		if(this.executed == True): return False

		colorLog("Math/Random:", f"Value request for port: {cable.output.name}, from node: {cable.input.iface.title}")

		# Let's create the value for him
		this.input['Re-seed']()