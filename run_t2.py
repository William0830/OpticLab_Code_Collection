from pipython import GCSDevice, pitools
import numpy as np
import time
import sys 
import auto_emailer as emailer
from datetime import datetime


from hydraharp_intensities3 import HH400_Histo_Manager




with HH400_Histo_Manager(mode=2) as HH400: 
    HH400.t2_meas(r'C:\Users\spmno\OneDrive\Documents\spm\Intensity Traces\goo0d.out', 100000)
    HH400.__exit__()


#HH400.__exit__()

#HH400.t2_meas('god.out', 10000)

# x=50 # Point you want to measure
# y=50 
# z_focus= 0 # In case you changed the focus or want to 

# # Needs a way to set mode and sync rate in here
# run_number=1 
# tacq=10000 # acquistion time in ms
# experiment_title = 'pq{}'.format(run_number)
# email_address = 'spmnotif@gmail.com'
# send_email = 1
# predelay = 0 #s
# parse_now = False # For future use, will set a flag that will pass your measured file to the parser immediately

# today = datetime.today().strftime('%Y-%m-%d')
# meas_name='{}_{}'.format(today, experiment_title)

# # Specify controller and the stages to be connected to this controller.
# CONTROLLERNAME = 'E-727'
# STAGES = ['P-517.3CD', 'P-517.3CD', 'P-517.3CD'] # connect stages to axes

# def run_meas(x,y, z_focus, tacq, predelay):
#     with GCSDevice(CONTROLLERNAME) as pidevice, HH400_Histo_Manager() as HH400, open(save_file, 'w') as t2file:
#         pos={'1':x,'2':y, '3':z_focus}
#         # Connect to the controller
#         pidevice.ConnectUSB(serialnum='0120036309')
#         pitools.startup(pidevice, stages=STAGES, refmodes=None)
#         print('Connected to piezo stage...')
#         print("Moving to point:%.3f, %.3f,%.3f",x,y,z_focus)
#         pidevice.MOV(pos) # Move to desired point
#         time.sleep(1.5) # Wait for axes to finish motion
#         real_pos = pidevice.qPOS()
#         print("TTTR Measurement beginning in %d seconds", predelay)
#         time.sleep(predelay)
#         print('Starting T2 measurement...')
#         HH400.t2_meas(t2file, tacq)
