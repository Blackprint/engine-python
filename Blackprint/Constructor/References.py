from .Port import Port
from .PortLink import PortLink

class References:
	IInput: dict[str, Port]
	Input: dict[str, PortLink]
	IOutput: dict[str, Port]
	Output: dict[str, PortLink]