from .Port import Port
from .PortLink import PortLink

class References:
	IInput: dict[str, Port] = None
	Input: dict[str, PortLink] = None
	IOutput: dict[str, Port] = None
	Output: dict[str, PortLink] = None