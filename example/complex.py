from .. import Blackprint
from pathlib import Path

# The nodes and interface is almost similar with the engine-js example
# When creating your own interface please use specific interface naming
# 'BPIC/LibraryName/FeatureName/NodeName'

# Because Python did support dynamic import
# our nodes in BPNode folders like this.. only used nodes that will be imported
Blackprint.registerNamespace(Path(__file__).resolve().parent+'/BPNode')

# == Import JSON after all nodes was registered ==
# You can import the JSON to Blackprint Sketch if you want to view the nodes visually
instance = Blackprint.Engine()
instance.importJSON('{"_":{"moduleJS":["http://localhost:6789/dist/nodes-example.mjs"],"functions":{"Test":{"id":"Test","title":"Test","description":"No description","vars":["shared"],"privateVars":["private"],"structure":{"BP/Fn/Input":[{"i":0,"x":389,"y":100,"z":3,"output":{"A":[{"i":2,"name":"A"}],"Exec":[{"i":2,"name":"Exec"}]}}],"BP/Fn/Output":[{"i":1,"x":973,"y":228,"z":14}],"Example/Math/Multiply":[{"i":2,"x":656,"y":99,"z":8,"output":{"Result":[{"i":3,"name":"Val"},{"i":9,"name":"Val"}]}},{"i":10,"x":661,"y":289,"z":4,"output":{"Result":[{"i":5,"name":"Val"},{"i":1,"name":"Result1"}]}}],"BP/Var/Set":[{"i":3,"x":958,"y":142,"z":9,"data":{"name":"shared","scope":2}},{"i":5,"x":971,"y":333,"z":2,"data":{"name":"private","scope":1},"route":{"i":1}}],"BP/Var/Get":[{"i":4,"x":387,"y":461,"z":5,"data":{"name":"shared","scope":2},"output":{"Val":[{"i":8,"name":"Any"}]}},{"i":6,"x":389,"y":524,"z":0,"data":{"name":"private","scope":1},"output":{"Val":[{"i":8,"name":"Any"}]}}],"BP/FnVar/Input":[{"i":7,"x":387,"y":218,"z":7,"data":{"name":"B"},"output":{"Val":[{"i":2,"name":"B"}]}},{"i":11,"x":386,"y":301,"z":6,"data":{"name":"Exec"},"output":{"Val":[{"i":10,"name":"Exec"}]}},{"i":12,"x":386,"y":370,"z":10,"data":{"name":"A"},"output":{"Val":[{"i":10,"name":"A"},{"i":10,"name":"B"}]}}],"Example/Display/Logger":[{"i":8,"x":661,"y":474,"z":11}],"BP/FnVar/Output":[{"i":9,"x":956,"y":69,"z":1,"data":{"name":"Result"}},{"i":14,"x":969,"y":629,"z":13,"data":{"name":"Clicked"}}],"Example/Button/Simple":[{"i":13,"x":634,"y":616,"z":12,"output":{"Clicked":[{"i":14,"name":"Val"}]}}]}}}},"Example/Math/Random":[{"i":0,"x":512,"y":76,"z":0,"output":{"Out":[{"i":5,"name":"A"}]},"route":{"i":5}},{"i":1,"x":512,"y":242,"z":1,"output":{"Out":[{"i":5,"name":"B"}]}}],"Example/Display/Logger":[{"i":2,"x":986,"y":282,"z":2,"id":"myLogger"}],"Example/Button/Simple":[{"i":3,"x":244,"y":64,"z":6,"id":"myButton","output":{"Clicked":[{"i":5,"name":"Exec"}]}}],"Example/Input/Simple":[{"i":4,"x":238,"y":279,"z":4,"id":"myInput","data":{"value":"saved input"},"output":{"Changed":[{"i":1,"name":"Re-seed"}],"Value":[{"i":2,"name":"Any"}]}}],"BPI/F/Test":[{"i":5,"x":738,"y":138,"z":5,"output":{"Result1":[{"i":2,"name":"Any"}],"Result":[{"i":2,"name":"Any"}],"Clicked":[{"i":6,"name":"Exec"}]},"route":{"i":6}}],"Example/Math/Multiply":[{"i":6,"x":1032,"y":143,"z":3}]}')

# Because lack of getter and setter feature, we need to get or set like calling a function
# Anyway.. lets to run something
button = instance.iface['myButton']

print("\n\n>> I'm clicking the button")
button.clicked(123)

logger = instance.iface['myLogger']
print("\n\n>> I got the output value: " + logger.log)

print("\n\n>> I'm writing something to the input box")
input = instance.iface['myInput']
input.data.value = 'hello wrold'

# you can also use getNodes if you haven't set the ID
logger = instance.getNodes('Example/Display/Logger')[0].iface
print("\n\n>> I got the output value: " + logger.log)