import Blackprint
import types
from ...utils import colorLog

@Blackprint.registerNode('Example/Input/Simple')
class Simple(Blackprint.Node):
	output = {
		'Changed': types.FunctionType,
		'Value': str,
	}

	def __init__(this, instance):
		Blackprint.Node.__init__(this, instance)

		iface = this.setInterface('BPIC/Example/Input')
		iface.title = "Input"

	# Bring value from imported iface to node output
	def imported(this, data):
		val = data['value']
		if(val): colorLog("Input/Simple:", f"Imported data: {val}")

		this.iface.data.value = val

class InputIFaceData:
	def __init__(this, iface):
		this._iface = iface
		this._data = {"value": '...'}

	@property
	def value(this):
		return this._data['value']

	@value.setter
	def value(this, val):
		this._data['value'] = val
		this._iface.changed(val)

@Blackprint.registerInterface('BPIC/Example/Input')
class InputIFace(Blackprint.Interface):
	def __init__(this, node):
		super(InputIFace, this).__init__(node)
		this.data = InputIFaceData(this)

	def changed(this, val):
		node = this.node

		# This node still being imported
		if(this.importing != False):
			return

		colorLog("Input/Simple:", f"The input box have new value: {val}")
		node.output['Value'] = val
		node.syncOut('data', {'value': this.data.value})

		# This will call every connected node
		node.output['Changed']()