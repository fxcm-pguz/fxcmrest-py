from enum import Enum
class State(Enum):
	DISCONNECTED = 1
	CONNECTING = 2
	CONNECTED = 3
	DISCONNECTING = 4
