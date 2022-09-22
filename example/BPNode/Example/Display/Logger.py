import json
from ..... import Blackprint
from .... import utils

@Blackprint.registerNode('Example/Display/Logger')
class Logger(Blackprint.Node):
	input = {
		'Any': Blackprint.Port.ArrayOf(Blackprint.Types.Any)
	}

	def __init__(this, instance):
		super(Logger, this).__init__(instance)

		iface = this.setInterface('BPIC/Example/Logger')
		iface.title = "Logger"

	def init(this):
		iface = this.iface

		def refreshLogger(val):
			if(val == None):
				val = 'None'
				iface.log(val)
			elif(isinstance(val, str) or isinstance(val, int)):
				iface.log(val)
			else:
				val = json.dumps(val)
				iface.log(val)

		def onCableConnection():
			utils.colorLog("Display/Logger:", "A cable was changed on Logger, now refresing the input element")
			refreshLogger(this.input['Any']())

		# Let's show data after new cable was connected or disconnected
		iface.on('cable.connect cable.disconnect', onCableConnection)

		def onAnyValue(ev):
			target = ev.target

			utils.colorLog("Display/Logger:", "I connected to {$target.name} (port {$target.iface.title}), that have new value: $target.value")

			# Let's take all data from all connected nodes
			# Instead showing new single data. val
			refreshLogger(this.input['Any']())

		iface.input['Any'].on('value', onAnyValue)

Logger.input['Any'] = Blackprint.Port.ArrayOf(Blackprint.Types.Any)

@Blackprint.registerInterface('BPIC/Example/Logger')
class LoggerIFace(Blackprint.Interface):
	_log = None
	def log(this, val = None): # getter (if first arg is None), setter (if not None)
		if(val == None): return this._log

		this._log = val
		utils.colorLog("Example/Logger log =>", val)