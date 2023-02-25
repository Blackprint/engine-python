# 0.8.12

### Features
- Add `initPorts` for dynamically initializing ports
- Emit `destroy` event when the instance was destroyed
- Add experimental feature to lock the instance
- Improve security for environment variable node by using connection rule
- Add experimental `Blackprint.Types.Slot` for ports with lazy type assignment
- Add event nodes feature
- Handle namespaced variable or nodes

### Bug Fix
- Emit internal event when function port was renamed
- Fix event to be emitted to root instance
- Fix function node that was not being initialized if created manually at runtime
- Fix route port connection and array input data
- Immediate init interface for single node creation
- Improve performance and fix execution order for with `StructOf` feature
- Reset updated cable status when disconnected
- Save port configuration and use it for creating function port
- Improve code for step mode execution
- Replace dot settings's internal save name with underscore
- Disable port manipulation on locked instance
- Put id as title if doesn't have custom title
- Avoid calling update on cable connection when the node having input route
- Remove internal marker to avoid dynamic port connection on outer function port
- Fix node update using default input value when cable was disconnected
- Fix dynamic port marker on internal interface
- Fix type assigned on variable node
- Force output port that use union to be Any type
- Move port type re-assigment for output port
- Improve output port's type when using port feature
- Validate namespace name
- Add options to disable cleaning the instance when importing JSON

# 0.8.0

Blackprint Engine for Python that was implemented from `engine-js` and `engine-php`