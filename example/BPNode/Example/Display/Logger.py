import json
import Blackprint
from ...utils import colorLog

@Blackprint.registerNode('Example/Display/Logger')
class Logger(Blackprint.Node):
	iface: 'LoggerIFace' = None
	input = {
		'Any': Blackprint.Port.ArrayOf(Blackprint.Types.Any)
	}

	def __init__(this, instance):
		super(Logger, this).__init__(instance)

		iface = this.setInterface('BPIC/Example/Logger')
		iface.title = "Logger"

	def refreshLogger(this, val):
		if(val == None):
			val = 'None'
			this.iface.log = val
		elif(isinstance(val, str) or isinstance(val, int)):
			this.iface.log = val
		else:
			val = json.dumps(val)
			this.iface.log = val

	def init(this):
		def onCableConnection():
			colorLog("Logger ("+(this.iface.id or '')+"):", "A cable was changed on Logger, now refresing the input element")

		# Let's show data after new cable was connected or disconnected
		this.iface.on('cable.connect cable.disconnect', onCableConnection)

		def onAnyValue(ev):
			target = ev.target

			colorLog("Logger ("+(this.iface.id or '')+"):", f"I connected to {target.name} ({target.iface.namespace}), that have new value: {target.value}")

		this.iface.input['Any'].on('value', onAnyValue)

	def update(this, cable):
		# Let's take all data from all connected nodes
		# Instead showing new single data-> val
		this.refreshLogger(this.input['Any'])

	# Remote sync in
	def syncIn(this, id, data):
		if(id == 'log'): this.iface.log = data


@Blackprint.registerInterface('BPIC/Example/Logger')
class LoggerIFace(Blackprint.Interface):
	_log = '...'

	@property
	def log(this):
		return this._log

	@log.setter
	def log(this, val):
		this._log = val
		colorLog("Logger ("+(this.id or '')+") Data:", val)
		this.node.syncOut('log', val)