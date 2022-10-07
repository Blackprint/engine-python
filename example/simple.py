import Blackprint
import BPNode # Register our nodes from BPNode folder

# == Import JSON after all nodes was registered ==
# You can import the JSON to Blackprint Sketch if you want to view the nodes visually
instance = Blackprint.Engine()
instance.importJSON('{"Example/Math/Random":[{"i":0,"x":298,"y":73,"z":0,"output":{"Out":[{"i":2,"name":"A"}]}},{"i":1,"x":298,"y":239,"z":1,"output":{"Out":[{"i":2,"name":"B"}]}}],"Example/Math/Multiply":[{"i":2,"x":525,"y":155,"z":2,"output":{"Result":[{"i":3,"name":"Any"}]}}],"Example/Display/Logger":[{"i":3,"x":763,"y":169,"z":3,"id":"myLogger","input":{"Any":[{"i":5,"name":"Value"},{"i":2,"name":"Result"}]}}],"Example/Button/Simple":[{"i":4,"x":41,"y":59,"z":4,"id":"myButton","output":{"Clicked":[{"i":2,"name":"Exec"}]}}],"Example/Input/Simple":[{"i":5,"x":38,"y":281,"z":5,"id":"myInput","data":{"value":"saved input"},"output":{"Changed":[{"i":1,"name":"Re-seed"}],"Value":[{"i":3,"name":"Any"}]}}]}')

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