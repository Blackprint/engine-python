import asyncio
from ..Utils import Utils

class CustomEvent:
	def __init__(this):
		this._events = {}
		this._once = {}

	def on(this, eventName, func, once = False):
		if(' ' in eventName):
			eventName = eventName.split(' ')

			for val in eventName:
				this.on(val, func, once)

			return

		if(once == False):
			events = this._events
		else:
			events = this._once

		if(eventName not in events):
			events[eventName] = []

		events[eventName].append(func)

	def once(this, eventName, func):
		this.on(eventName, func, True)

	def waitOnce(this, eventName):
		loop = asyncio.get_running_loop()
		fut = loop.create_future()

		def func(ev): fut.set_result(ev)
		this.on(eventName, func, True)

		return fut

	def off(this, eventName, func = None):
		if(' ' in eventName):
			eventName = eventName.split(' ')

			for val in eventName:
				this.off(val, func)

			return

		if(func == None):
			del this._events[eventName]
			del this._once[eventName]
			return

		if(eventName not in this._events): return

		i = Utils.findFromList(this._events[eventName], func)
		if(i != False):
			this._events[eventName].pop(i)

		i = Utils.findFromList(this._once[eventName], func)
		if(i != False):
			this._once[eventName].pop(i)

	def emit(this, eventName, data=None):
		events = this._events
		once = this._once

		if(eventName in events):
			evs = events[eventName]
			for val in evs:
				val(data)

		if(eventName in once):
			evs = once[eventName]
			for val in evs:
				val(data)

			del once[eventName]