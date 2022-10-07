<p align="center"><a href="#" target="_blank" rel="noopener noreferrer"><img width="150" src="https://user-images.githubusercontent.com/11073373/141421213-5decd773-a870-4324-8324-e175e83b0f55.png" alt="Blackprint"></a></p>

<h1 align="center">Blackprint Engine for Python</h1>
<p align="center">Run exported Blackprint on Python environment.</p>

<p align="center">
    <a href='https://github.com/Blackprint/Blackprint/blob/master/LICENSE'><img src='https://img.shields.io/badge/License-MIT-brightgreen.svg' height='20'></a>
</p>

## Documentation
> Warning: This project haven't reach it stable version (semantic versioning at v1.0.0)<br>
> But please try to use it and help improve this project

This engine is designed to be similar with `engine-js`, some API and property will be similar.

**Minimum Python version `>= 3.10`**

```sh
$ pip install blackprint-engine
```

---

### Defining Blackprint Node and Interface
Because Python does support class-based programming and to make the node import more effective and easier, this engine will only support Node/Interface that declared with classes.

But before that, we need to create a folder to store our Node/Interface logic. For the example `/BPNode`. And then import it like below:

```python
import Blackprint
import BPNode # Import your own nodes located on ./BPNode directory
```

#### Defining custom node

```python
# file: ./BPNode/Example/Hello.py
import types

@Blackprint.registerNode('Example/Hello')
class Hello(Blackprint.Node):
    # Please remember to capitalize the port name
    # Set the output port structure for your node (Optional)
    output = {
        'Changed': types.FunctionType,
        # Callable -> this.output['Changed']()

        'Output': int,
        # this.output['Value'] = 246
    }

    # Set the input port structure for your node (Optional)
    input = {
        'Multiply': int,
        # val = this.output['Value']
    }

    def __init__(instance):
        # Call the parent constructor first, passing the instance (Blackprint.Engine)
        super(Hello, this).__init__(instance)

        # Set the Interface, let it empty if you want
        # to use default empty interface "setInterface()"
        iface = this.setInterface('BPIC/Example/Hello')
        iface.title = "Hello" # Set the title for debugging
```

Let's also define our custom interface, this is optional and needed only if you want to provide access for other developer. Just like an API (Application Programming Interface).

```python
# same file: ./BPNode/Example/Hello.py

# Your Interface namespace must use "BPIC" as the prefix
@Blackprint.registerInterface('BPIC/Example/Hello')
class HelloIFace(Blackprint.Interfaces):
    def __construct(node):
        # Call the parent constructor first, passing the node (Blackprint\Node)
        super(HelloIFace, this).__init__(node)
        # this.node => Blackprint.Node

        # Define IFace's data (optional if you want to export/import data from JSON)
        # Because getter/setter feature only available on class, we will create from `class MyData`
        this.data = MyData(this)
        # this.data.value == 123 (if the default value is not replaced when importing JSON)

    def recalculate():
        # Get value from input port
        multiplyBy = this.node.input['Multiply']

        # Assign new value to output port
        this.node.output['Output'] = this.data.value * multiplyBy

# Getter and setter should be changed with basic property accessor
class MyData:
    # Constructor promotion, iface as private MyData property
    def __init__(this, iface):
        this._iface = iface

    _value = 123

    @property
    def value();
        return this._value

    @value.setter
    def value(val);
        this._value = val
        this._iface.recalculate() # Call recalculate() on HelloIFace
```

## Creating new Engine instance

```python
# Create Blackprint Engine instance
instance = Blackprint.Engine()

# You can import nodes with JSON
# if the nodes haven't been registered, this will throw an error
instance.importJSON('{...}')

# You can also create the node dynamically
iface = instance.createNode('Example/Hello')

# ----

# Change the default data 'value' property
iface.data.value = 123

# Assign the 'Multiply' input port = 2
iface.node.input['Multiply'] = 2

# Get the value from 'Output' output port
print(iface.node.output['Output']) # 246
```

---

### Example
![csZIeKxr7j](https://user-images.githubusercontent.com/11073373/194294366-6a212509-d565-409c-81b5-763b0a3923ba.jpg)

This repository provide an example with the JSON too, and you can try it with Python 3:<br>

```sh
# Change your working directory into empty folder first
$ git clone --depth 1 https://github.com/Blackprint/engine-python .
$ pip install -e .
$ py ./example/simple.py
```
