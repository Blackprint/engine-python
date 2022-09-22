from ..... import Blackprint
from .... import utils

@Blackprint.registerNode('Example/Input/Simple')
class Simple(Blackprint.Node):
	output = {
		'Changed': Blackprint.Types.Function,
		'Value': Blackprint.Types.String,
	}

	def __init__(this, instance):
		super(Simple, this).__init__(instance)

		iface = this.setInterface('BPIC/Example/Input')
		iface.title = "Input"

	# Bring value from imported iface to node output
	def imported(this, data):
		val = data['value']
		if(val): utils.colorLog("Input/Simple:", "Imported data: {val}")

		this.iface.data.value = val

class InputIFaceData:
	def __init__(this, iface):
		this._iface = iface
		this._data = {"value": '...'}

	@property
	def value(this):
		return this._data.value

	@value.setter
	def value(this, val):
		this._data.value = val
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

		utils.colorLog("Input/Simple:", "The input box have new value: $val")
		node.output['Value'](val)
		node.syncOut('data', {'value' : this.data.value})

		# This will call every connected node
		node.output['Changed']()