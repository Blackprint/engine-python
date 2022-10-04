import Blackprint
import types
from ...utils import colorLog

@Blackprint.registerNode('Example/Dummy/UpdateTest')
class UpdateTest(Blackprint.Node):
	input = {
		'A1': str,
		'A2': str,
	}
	output = {
		'B1': str,
		'B2': str,
	}

	def __init__(this, instance):
		super(UpdateTest, this).__init__(instance)

		iface = this.setInterface() # Let's use default node interface
		iface.title = "Pass data only"

		# def onValue(ev):
		# 	if(ev.port.source != 'input'): return
		# 	this[ev.port.name] = ev.target.value
		
		# iface.on('port.value', onValue)

	async def update(this, cable):
		# index = this.iface.id or this.instance.ifaceList.index(this.iface)
		# print("UpdateTest "+index+"> Updating ports")

		# if(this.input['A1'] != this['A1']): print("A1 from event listener value was mismatched")
		# if(this.input['A2'] != this['A2']): print("A2 from event listener value was mismatched")

		this.output['B1'] = this.input['A1']
		this.output['B2'] = this.input['A2']
		# print("UpdateTest "+index+"> Updated")