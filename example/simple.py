import Blackprint
import BPNode # Register our nodes from BPNode folder

import sys
sys.tracebacklimit = 2

# == Import JSON after all nodes was registered ==
# You can import the JSON to Blackprint Sketch if you want to view the nodes visually
instance = Blackprint.Engine()
instance.importJSON('{"instance":{"Example/Math/Random":[{"i":0,"x":298,"y":73,"output":{"Out":[{"i":2,"name":"A"}]}},{"i":1,"x":298,"y":239,"output":{"Out":[{"i":2,"name":"B"}]}}],"Example/Math/Multiply":[{"i":2,"x":525,"y":155,"output":{"Result":[{"i":3,"name":"Any"}]}}],"Example/Display/Logger":[{"i":3,"id":"myLogger","x":763,"y":169}],"Example/Button/Simple":[{"i":4,"id":"myButton","x":41,"y":59,"output":{"Clicked":[{"i":2,"name":"Exec"}]}}],"Example/Input/Simple":[{"i":5,"id":"myInput","x":38,"y":281,"data":{"value":"saved input"},"output":{"Changed":[{"i":1,"name":"Re-seed"}],"Value":[{"i":3,"name":"Any"}]}}]},"moduleJS":["https://cdn.jsdelivr.net/npm/@blackprint/nodes@0.7/dist/nodes-example.mjs"]}')

# Lets to run something
button = instance.iface['myButton']

print("\n>> I'm clicking the button")
button.clicked()

logger = instance.iface['myLogger']
print("\n>> I got the output value: " + logger.log)

print("\n>> I'm writing something to the input box")
input = instance.iface['myInput']
input.data.value = 'hello wrold'

# you can also use getNodes if you haven't set the ID
logger = instance.getNodes('Example/Display/Logger')[0].iface
print("\n>> I got the output value: " + logger.log)