import Blackprint
import types
from ...utils import colorLog

@Blackprint.registerNode('Example/Button/Simple')
class Simple(Blackprint.Node):
	output = {
		'Clicked': types.FunctionType
	}

	def __init__(this, instance):
		super(Simple, this).__init__(instance)

		iface = this.setInterface('BPIC/Example/Button')
		iface.title = "Button"

@Blackprint.registerInterface('BPIC/Example/Button')
class ButtonIFace(Blackprint.Interface):
	def clicked(this, ev = None):
		colorLog("Button/Simple:", "'Trigger' button clicked")
		this.node.output['Clicked']()