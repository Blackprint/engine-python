import asyncio
from ..Utils import Utils

class CustomEvent:
	def __init__(this):
		this._events = {}
		this._once = {}
		this._eventsMultiListen = None # Collection of function that listening to multiple event in a single function

	def on(this, eventName, func, once = False):
		if(' ' in eventName):
			eventName = eventName.split(' ')

			if(this._eventsMultiListen == None): this._eventsMultiListen = set()
			this._eventsMultiListen.add(func)

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
		elif(this._eventsMultiListen != None):
			this._eventsMultiListen.discard(func)

		if(eventName in this._events):
			_events = this._events[eventName]
			i = Utils.findFromList(_events, func)
			if(i != None):
				_events.pop(i)

		if(eventName in this._once):
			_once = this._once[eventName]
			i = Utils.findFromList(_once, func)
			if(i != None):
				_once.pop(i)

	def emit(this, eventName, data=None):
		events = this._events
		once = this._once

		if(eventName in events):
			evs = events[eventName]
			for val in evs:
				if(this._eventsMultiListen != None and val in this._eventsMultiListen):
					val(data, eventName)
				else: val(data)

		if(eventName in once):
			evs = once[eventName]
			for val in evs:
				if(this._eventsMultiListen != None and val in this._eventsMultiListen):
					val(data, eventName)
				else: val(data)

			del once[eventName]