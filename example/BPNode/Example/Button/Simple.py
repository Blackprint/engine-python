import Blackprint
from ..utils import colorLog

@Blackprint.registerNode('Example/Button/Simple')
class Simple(Blackprint.Node):
	output = {
		'Clicked': Blackprint.Types.Trigger
	}

	# Create interface for puppet node
	interfaceSync = [
		{'type': "button_in", 'id': "click", 'text': "Trigger", 'tooltip': "Trigger", 'inline': True}
	]

	def __init__(this, instance):
		super(Simple, this).__init__(instance)

		iface = this.setInterface('BPIC/Example/Button')
		iface.title = "Button"

	# Remote sync in
	def syncIn(this, id, data):
		if(id == 'click' and data['press'] == False): this.iface.clicked()

@Blackprint.registerInterface('BPIC/Example/Button')
class ButtonIFace(Blackprint.Interface):
	def clicked(this, ev = None):
		colorLog("Button/Simple:", "'Trigger' button clicked")
		this.node.output['Clicked']()
		this.node.syncOut('click', {'press': False})