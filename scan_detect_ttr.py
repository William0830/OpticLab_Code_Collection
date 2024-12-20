from run_scan_5 import run_scan
from Yolo_helper import detect_boxes_and_centers,get_qdot_coordinates,image_preprocessing
import time
import sys
import os
from PIL import Image
from datetime import datetime
from pipython import GCSDevice, pitools
#from collections import OrderedDict
import scan_plot_and_analysis as spa
import matplotlib.pyplot as plt
import matplotlib as mpl
from hydraharp_intensities3 import HH400_Histo_Manager
import random
import json
import uuid
from Yolo_helper import plot_intensity_map_with_boxes

# Scan Parameters
z_focus =10 # µm
xlim = (45, 60) # µm
ylim = (60,75) # µm
resolution = .5 # um
exp_num = 15

tacq = 100 # ms #Used in tttrmode
experiment_title = 'pq{}'.format(exp_num)
email_address = 'spmnotif@gmail.com'
send_email = 0
predelay = 0 # s
show_plot = True
intensity_histograms=False
show_scan_stats = True
require_user_input = False
vmin, vmax = 0, 50000

# naming convention
today = datetime.today().strftime('%Y-%m-%d')
scan_name = '{}_{}'.format(today, experiment_title)

# Specify controller and the stages to be connected to this controller.
CONTROLLERNAME = 'E-727'
STAGES = ['P-517.3CD', 'P-517.3CD', 'P-517.3CD'] # connect stages to axes


#Yolo parameters
yolo_model_path = 'best_yolo.pt'
yolo_conf_threshold = 0.1

# naming convention
today = datetime.today().strftime('%Y-%m-%d')
scan_name = '{}_{}'.format(today, experiment_title)


def tttr_scan_loop(qdot_coords,root_folder,tacq,autozero=False,position_error_threshold=0.05,allowed_time_in_minutes=360,shuffle=False):
    if shuffle:
        random.shuffle(qdot_coords)
    # Monitor the time it takes for the tttr_scan to run, break the loop if time exceeded the limit
    start_time = time.time()
    allowed_time_in_seconds = allowed_time_in_minutes * 60
    #check if the given directory exists, if not, make one
    if not qdot_coords:
        raise Exception('The coordinates list is empty')
    ######## save path is the folder where all tttr data will be stored
    save_path = r'{}\{}'.format(root_folder,'tttr_scan'+experiment_title)
    if not os.path.isdir(save_path):
        os.mkdir(save_path)
    with GCSDevice(CONTROLLERNAME) as pidevice:
        ########## Connect to and Initialize Piezo ##########
        pidevice.ConnectUSB(serialnum='0120036309')
        pitools.startup(pidevice, stages=STAGES, refmodes=None)
        if autozero:
            pidevice.ATZ()  # autozero
            pitools.waitonautozero(pidevice)
        time.sleep(5)  # Wait for the Controller to be ready
        print('Connected to piezo stage...')
        total_scan = len(qdot_coords)
        for index, coord in enumerate(qdot_coords):
            x_coord = coord[0]
            y_coord = coord[1]
            position = {'1':x_coord,'2':y_coord,'3':z_focus}
            pidevice.MOV(position)  # move to start position
            time.sleep(3)  # wait for axes to finish motion
            #Check if the the stage is behaving normal
            real_position = pidevice.qPOS() # get real position
            if abs(real_position['1']-x_coord) > position_error_threshold or abs(real_position['2']-y_coord) > position_error_threshold:
                raise Exception('The stage is not at the right position.')
            else:
                print(f"Moved to Scan Position {index}/{total_scan},real position x:{real_position['1']},y:{real_position['2']}")
            with HH400_Histo_Manager(mode=2,send_error_email=send_email) as HH400:
                # Ensure the file is saved at the designated folder
                base_filename = f'qdot{index}'
                filename = os.path.join(save_path,base_filename)
                HH400.t2_meas(filename=filename,tacq=tacq)
                print(f"Scan {index}/{total_scan} finished")
            current_time = time.time()
            time_elapsed = current_time -start_time
            if time_elapsed > allowed_time_in_seconds:
                print(f"Scan has exceeded time limit.Progress{index}/{total_scan} ")
                break
            else:
                continue
        print("Scanning completed.")
    print("pidevice disconnected")
    return None






if __name__ == '__main__':
    print("Scan started")
    # Check if File name already exists
    rel_path = r'C:\Users\spmno\OneDrive\Documents\spm\Scan\Scan Data\{}'.format(today)
    if not os.path.isdir(rel_path):
        os.mkdir(rel_path)

    save_file = "{}\{}_scan_data.txt".format(rel_path, scan_name)
    if os.path.isfile(save_file):
        raise Exception("File name already exists!")
    if ylim[1] < ylim[0] or xlim[1] < xlim[0]:
        raise Exception("Invalid scan area! Limits must be in increasing order!")

    # Run Scan
    t1 = time.time()
    Xs, Ys, intensity, intensity_split, t_estim = run_scan(xlim, ylim, z_focus, resolution, tacq, save_file, vmin, vmax,
                                                           predelay, autozero=False, send_email=send_email)
    plot_name_root = '{}/{}'.format(rel_path, scan_name)
    spa.plot_int_heatmap(Xs, Ys, intensity, save=True, save_name='{}.png'.format(plot_name_root))
    spa.plot_int_heatmap(Xs, Ys, intensity_split[0], save=True, save_name='{}_ch1.png'.format(plot_name_root))
    spa.plot_int_heatmap(Xs, Ys, intensity_split[1], save=True, save_name='{}_ch2.png'.format(plot_name_root))
    t2 = time.time()



    #Preprocess the image to feed the Yolo model
    intensity_processed = image_preprocessing(intensity,local_normalize=False)
    boxes,centers = detect_boxes_and_centers(image_input=intensity_processed,model_path=yolo_model_path,conf_threshold=0.1)
    plot_intensity_map_with_boxes(intensity_map=intensity,boxes=boxes)
    qdot_coords = get_qdot_coordinates(image=intensity_processed,Xs=Xs,Ys=Ys,model_path=yolo_model_path,conf=yolo_conf_threshold)


    if not qdot_coords:
        raise Exception('No quantum dots found in the scan')
    # Convert to a dictionary with index and coord,generate an id for unique identification
    quantum_dots_dict = {"data": [{"index": i, "coord": coord,"id":str(uuid.uuid4())} for i, coord in enumerate(qdot_coords)]}
    # Specify the output file name
    output_filename_base = f"quantum_dots_{experiment_title}.json"
    output_filename = os.path.join(rel_path,output_filename_base)
    # Save to a JSON file
    with open(output_filename, "w") as json_file:
        json.dump(quantum_dots_dict, json_file, indent=4)
    print(f"Data saved to {output_filename}")


    # Loop through the quantum dot position to run tttr scan
    tttr_scan_loop(qdot_coords=qdot_coords,root_folder=rel_path,tacq=1000)




