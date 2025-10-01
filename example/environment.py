import Blackprint
# import BPNode # Register our nodes from BPNode folder

import sys
sys.tracebacklimit = 2

Blackprint.ModuleLoader.add_path('BPNode/Example') # Register our nodes from BPNode folder

Blackprint.Environment.set('TEST', '12345')
Blackprint.Environment.imports({ 'TEST2': '54321' })
Blackprint.Environment.rule('TEST2', {
	'allowGet': [], # empty = disable any connection
	# 'allowGet'=> [], # empty = disable any connection
})

# == Import JSON after all nodes was registered ==
# You can import the JSON to Blackprint Sketch if you want to view the nodes visually
instance = Blackprint.Engine()
instance.importJSON('{"instance":{"BP/Env/Get":[{"i":0,"x":249,"y":190,"z":2,"id":"testOut","data":{"name":"TEST"},"output":{"Val":[{"i":4,"name":"Any","parentId":0}]},"_cable":{"Val":[{"x":407,"y":282,"branch":[{"id":0}]}]}},{"i":2,"x":484,"y":188,"z":3,"id":"test2Out","data":{"name":"TEST2"}}],"BP/Env/Set":[{"i":1,"x":248,"y":140,"z":1,"id":"test","data":{"name":"TEST"},"input_d":{"Val":""}},{"i":3,"x":483,"y":138,"z":0,"id":"test2","data":{"name":"TEST2"},"input_d":{"Val":""}}],"Example/Display/Logger":[{"i":4,"x":646,"y":232,"z":4,"id":"myLogger"}]},"moduleJS":["http://localhost:6789/dist/nodes-example.mjs"]}')

TEST = instance.iface['test'] # input
TEST_ = instance.iface['testOut'] # output
TEST2 = instance.iface['test2'] # input
TEST2_ = instance.iface['test2Out'] # output

logger = instance.iface['myLogger']
print("\n>> I got the output value: " + logger.log)

print("\n\n>> I'm writing env value 'hello' into the node")
out = Blackprint.OutputPort(str)
out.value = 'hello'
TEST.ref.IInput['Val'].connectPort(out)
print("\n>> I got the output value: " + logger.log)

print("\n\n>> I'm trying to connect ruled environment node, this must can't be connected")
try:
	TEST2_.output['Val'].connectPort(logger.input['Any'])
	print("Error: the cable was connected")
except Exception:
	print("Looks OK")