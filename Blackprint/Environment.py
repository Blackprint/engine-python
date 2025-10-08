import re
from typing import Dict

from .Internal import EvEnv, EvEnvRenamed
from .Event import Event

class Environment:
	_noEvent = False # static property
	map: Dict[str, str] = {} # static property
	_rules: Dict[str, str] = {} # static property

	# arr = ["KEY": "value"]
	@staticmethod
	def imports(arr: Dict[str, str]):
		Environment._noEvent = True
		for key, value in arr.items():
			Environment.set(key, value)

		Environment._noEvent = False
		Event.emit('environment.imported')

	@staticmethod
	def set(key, val: str):
		if(re.search(r"[^A-Z_][^A-Z0-9_]", key) != None):
			raise Exception(f"Environment must be uppercase and not contain any symbol except underscore, and not started by a number. But got: {key}")

		if(type(val) != str):
			raise Exception(f"Environment value must be a string (found \"{val}\" in {key})")

		Environment.map[key] = val

		if(not Environment._noEvent):
			temp = EvEnv(key, val)
			Event.emit('environment.added', temp)

	@staticmethod
	def delete(key):
		if key in Environment.map:
			del Environment.map[key]

		temp = EvEnv(key)
		Event.emit('environment.deleted', temp)

	@staticmethod
	def _rename(keyA, keyB):
		if(not keyB): return

		if(re.search(r"[^A-Z_][^A-Z0-9_]", keyB) != None):
			raise Exception(f"Environment must be uppercase and not contain any symbol except underscore, and not started by a number. But got: {keyB}")

		if keyA not in Environment.map:
			raise Exception(f"{keyA} was not defined in the environment")

		Environment.map[keyB] = Environment.map[keyA]
		del Environment.map[keyA]

		Event.emit('environment.renamed', EvEnvRenamed(keyA, keyB))


	# options = {allowGet: {}, allowSet: {}}
	@staticmethod
	def rule(name, options):
		if(name not in Environment.map):
			raise Exception(f"'{name}' was not found on Blackprint.Environment, maybe it haven't been added or imported")

		if(name in Environment._rules):
			raise Exception(f"'rule' only allow first registration")

		Environment._rules[name] = options