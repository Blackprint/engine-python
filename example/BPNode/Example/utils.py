import os
os.system('color')

def colorLog(category, message=''):
	# Color definitions
	colors = {
		'reset': "\033[0m",
		'red': "\033[31m",
		'green': "\033[32m",
		'yellow': "\033[33m",
		'blue': "\033[34m",
		'magenta': "\033[35m",
		'cyan': "\033[36m",
		'white': "\033[37m",
	}

	# Determine category color
	category_color = colors['cyan']
	if 'Button' in category:
		category_color = colors['blue']
	elif 'Logger' in category:
		category_color = colors['green']
	elif 'Input' in category:
		category_color = colors['yellow']
	elif 'Math' in category:
		category_color = colors['magenta']

	# Print formatted message
	print(f"{category_color}{category}{colors['reset']} {colors['white']}{message}{colors['reset']}")