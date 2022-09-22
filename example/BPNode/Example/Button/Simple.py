from ..... import Blackprint
from .... import utils

@Blackprint.registerNode('Example/Button')
class Simple(Blackprint.Node):
	output = {
		'Clicked': Blackprint.Types.Function
	}

	def __init__(this, instance):
		super(Simple, this).__init__(instance)

		iface = this.setInterface('BPIC/Example/Button')
		iface.title = "Button"

@Blackprint.registerInterface('BPIC/Example/Button')
class ButtonIFace(Blackprint.Interface):
	def clicked(this, ev = None):
		utils.colorLog("Button/Simple:", "'Trigger' button clicked")
		this.node.output.Clicked()