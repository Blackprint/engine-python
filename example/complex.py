import asyncio
import Blackprint
# import BPNode # Register our nodes from BPNode folder

import sys
sys.tracebacklimit = 2

Blackprint.ModuleLoader.add_path('BPNode/Example') # Register our nodes from BPNode folder

# == Import JSON after all nodes was registered ==
# You can import the JSON to Blackprint Sketch if you want to view the nodes visually
instance = Blackprint.Engine()
instance.importJSON('{"instance":{"Example/Math/Random":[{"i":0,"x":358,"y":80,"z":0,"output":{"Out":[{"i":5,"name":"A"},{"i":7,"name":"Any"}]},"route":{"i":7}},{"i":1,"x":358,"y":246,"z":1,"output":{"Out":[{"i":5,"name":"B"},{"i":7,"name":"Any"}]}}],"Example/Display/Logger":[{"i":2,"x":935,"y":282,"z":5,"id":"myLogger","input":{"Any":[{"i":4,"name":"Value"},{"i":5,"name":"Result1"}]}},{"i":7,"x":626,"y":79,"z":3,"id":"mul_outer","input":{"Any":[{"i":0,"name":"Out"},{"i":1,"name":"Out"}]}}],"Example/Button/Simple":[{"i":3,"x":62,"y":138,"z":4,"id":"myButton","output":{"Clicked":[{"i":0,"name":"Re-seed"},{"i":5,"name":"Exec","parentId":0}]},"_cable":{"Clicked":[{"x":543,"y":176,"branch":[{"id":0}]}]}}],"Example/Input/Simple":[{"i":4,"x":83,"y":283,"z":2,"id":"myInput","data":{"value":"saved input"},"output":{"Changed":[{"i":1,"name":"Re-seed"}],"Value":[{"i":2,"name":"Any"}]}}],"BPI/F/Test":[{"i":5,"x":621,"y":209,"z":7,"output":{"Result1":[{"i":2,"name":"Any"}],"Clicked":[{"i":6,"name":"Exec"}]}}],"Example/Math/Multiply":[{"i":6,"x":940,"y":161,"z":6,"input_d":{"A":0}}]},"moduleJS":["http://localhost:6789/dist/nodes-example.mjs"],"functions":{"Test":{"title":"Test","description":"No description","vars":["shared"],"privateVars":["private"],"structure":{"instance":{"BP/Fn/Input":[{"i":0,"x":72,"y":100,"z":2,"output":{"A":[{"i":2,"name":"A"},{"i":13,"name":"Any"}],"Exec":[{"i":2,"name":"Exec"}],"B":[{"i":13,"name":"Any"}]}}],"BP/Fn/Output":[{"i":1,"x":656,"y":228,"z":10},{"i":15,"x":583,"y":603,"z":15,"input_d":{"Result1":0}}],"Example/Math/Multiply":[{"i":2,"x":339,"y":99,"z":7,"output":{"Result":[{"i":3,"name":"Val"}]}},{"i":9,"x":344,"y":289,"z":3,"output":{"Result":[{"i":5,"name":"Val"},{"i":1,"name":"Result1"}]}}],"BP/Var/Set":[{"i":3,"x":583,"y":112,"z":14,"data":{"name":"shared","scope":2}},{"i":5,"x":654,"y":333,"z":1,"data":{"name":"private","scope":1},"route":{"i":1}}],"BP/Var/Get":[{"i":4,"x":70,"y":461,"z":4,"data":{"name":"shared","scope":2},"output":{"Val":[{"i":8,"name":"Any"}]}},{"i":6,"x":72,"y":524,"z":0,"data":{"name":"private","scope":1},"output":{"Val":[{"i":8,"name":"Any"}]}}],"BP/FnVar/Input":[{"i":7,"x":70,"y":218,"z":6,"data":{"name":"B"},"output":{"Val":[{"i":2,"name":"B"},{"i":14,"name":"Any"}]}},{"i":10,"x":69,"y":301,"z":5,"data":{"name":"Exec"},"output":{"Val":[{"i":9,"name":"Exec"}]}},{"i":11,"x":69,"y":370,"z":8,"data":{"name":"A"},"output":{"Val":[{"i":9,"name":"A"},{"i":9,"name":"B"},{"i":14,"name":"Any"}]}}],"Example/Display/Logger":[{"i":8,"x":344,"y":474,"z":11,"id":"innerFunc","input":{"Any":[{"i":4,"name":"Val"},{"i":6,"name":"Val"}]}},{"i":13,"x":344,"y":196,"z":12,"id":"mul_inner1","input":{"Any":[{"i":0,"name":"A"},{"i":0,"name":"B"}]}},{"i":14,"x":345,"y":385,"z":13,"id":"mul_inner2","input":{"Any":[{"i":11,"name":"Val"},{"i":7,"name":"Val"}]}}],"Example/Button/Simple":[{"i":12,"x":317,"y":616,"z":9,"output":{"Clicked":[{"i":15,"name":"Clicked"}]}}]}}}}}')

# Lets to run something
button = instance.iface['myButton']

print("\n>> I'm clicking the button")
button.clicked()

logger = instance.iface['myLogger']
# logger.waitOnce('updated')
print("\n>> I got the output value: " + logger.log)

print("\n>> I'm writing something to the input box")
input = instance.iface['myInput']
input.data.value = 'hello wrold'

# you can also use getNodes if you haven't set the ID
logger = instance.getNodes('Example/Display/Logger')[0].iface
# logger.waitOnce('updated')
print("\n>> I got the output value: " + logger.log)