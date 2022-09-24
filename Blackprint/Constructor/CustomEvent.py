from .. import Utils

class CustomEvent:
	_events = []
	_once = []

	def on(this, eventName, func, once = False):
		if(' ' in eventName):
			eventName = eventName.split(' ')

			for val in eventName:
				this.on(val, func, once)

			return

		if(once == False):
			events = this.events
		else:
			events = this.once

		if(events.has_key(eventName) == False):
			events[eventName] = []

		events[eventName].append(func)

	def once(this, eventName, func):
		this.on(eventName, func, True)

	def off(this, eventName, func = None):
		if(' ' in eventName):
			eventName = eventName.split(' ')

			for val in eventName:
				this.off(val, func)

			return

		if(func == None):
			del this.events[eventName]
			del this.once[eventName]
			return

		if(not this.events.has_key(eventName)): return

		i = Utils.findFromList(func, this.events[eventName])
		if(i != False):
			this.events[eventName].pop(i)

		i = Utils.findFromList(func, this.once[eventName])
		if(i != False):
			this.once[eventName].pop(i)

	def emit(this, eventName, data=None):
		events = this.events
		once = this.once

		if(events.has_key(eventName)):
			evs = events[eventName]
			for val in evs:
				val(data)

		if(once.has_key(eventName)):
			evs = once[eventName]
			for val in evs:
				val(data)

			del once[eventName]