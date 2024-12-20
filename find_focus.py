import find_focus_functions as fff
import numpy as np
from datetime import datetime
from collections import OrderedDict

# Test parameters
exp_num = "1"
exp_name = 'test'
# File Naming Conventions
now = datetime.now()
date_time = now.strftime("%m-%d-%Y")
filename = '{}_{}_{}_{}'.format(date_time, 'focus_data', exp_name, exp_num)

# # # Modes: 'm', 'gcm', 'a', 'gca', 'ascan'
# # Manual Mode
# mode = 'a'
# start_pos = OrderedDict([('1', 90), ('2', 12.5), ('3', 10)]) # starting position
# filename = '{}_{}.txt'.format(filename, mode)
# fff.run_scan(start_pos, 'm', autozero=False, focus_data_fn=filename, block = 3)

# # Auto Mode
# mode = 'a'
# start_pos = OrderedDict([('1',87.6), ('2', 2.3), ('3', 0)]) # starting position
# filename = '{}_{}.txt'.format(filename, mode)
# fff.run_scan(start_pos, 'a', increment = 0.1, autozero=False, focus_data_fn=filename, block = 6)

# Auto Scan Mode
mode = 'm'
start_pos = OrderedDict([('1', 57.959), ('2', 74.446), ('3', 4.053)]) # starting position
filename = '{}_{}.txt'.format(filename, mode)
fff.run_scan(start_pos, 'm', autozero=False, focus_data_fn=filename)