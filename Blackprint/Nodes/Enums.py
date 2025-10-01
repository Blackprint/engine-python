class Enums:
	BPEnvGet = 1
	BPEnvSet = 2
	BPVarGet = 3
	BPVarSet = 4
	BPFnVarInput = 5
	BPFnVarOutput = 6  # Not used, but reserved
	BPFnInput = 7
	BPFnOutput = 8
	BPFnMain = 9
	BPEventListen = 10
	BPEventEmit = 11

	# InitUpdate constants for node initialization rules
	NoRouteIn = 2      # Only when no input cable connected
	NoInputCable = 4   # Only when no input cable connected
	WhenCreatingNode = 8  # When all the cable haven't been connected (other flags may be affected)