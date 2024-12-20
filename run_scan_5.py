from pipython import GCSDevice, pitools
#from collections import OrderedDict
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import time
import sys
import os
from PIL import Image
from datetime import datetime

from hydraharp_intensities2 import HH400_Histo_Manager
import scan_plot_and_analysis as spa
import auto_emailer as emailer


# Moving to (38.8, 37.3, 0)...
# Max intensity z positions (Sum, CH1, CH2): 10.099177, 11.599177, 10.399177

# Test parameters
# point = (25, 50, 10)
# change = 5
# resolution = 0.2
# exp_num = 20

# z_focus = point[2] # µm
# xlim = (point[0]-change, point[0] +change) # µm
# ylim = (point[1]-change, point[1]+change) # µm


z_focus =10 # µm
xlim = (15, 25) # µm
ylim = (55,65) # µm
resolution = .5 # um
exp_num = 3

tacq = 100 # ms #Deprecated in v5.0 and onwards
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

def run_scan(xlim, ylim, z_focus, resolution, tacq, save_file, vmin, vmax, predelay=0, autozero=False, send_email=False):
    """Connect, setup system and move stages and display the positions in a loop."""

    # major_axis_wait_time = 0.3 # seconds
    # minor_axis_wait_time = 0.14 # seconds
    major_axis_wait_time = 0.2 # seconds
    minor_axis_wait_time = 0.1 # seconds
    
    # scan points in x and y [x0, xf] x [y0, yf] (um); z is fixed;
    xnodes = np.linspace(xlim[0], xlim[1], int((xlim[1]-xlim[0])/resolution) + 1).round(decimals=3) # x coordinates [0, distx] (um)
    ynodes = np.linspace(ylim[0], ylim[1], int((ylim[1]-ylim[0])/resolution) + 1).round(decimals=3)

    Xs, Ys = np.meshgrid(xnodes, ynodes, indexing='ij')

    len_x = len(xnodes)
    len_y = len(ynodes)

    intensities = np.zeros((len_x, len_y)) # initialize array of intensities
    intensities_split = np.zeros((2, len_x, len_y))

    estimated_time = ((((xlim[1] - xlim[0])/resolution) * ((ylim[1] - ylim[0])/resolution))*.1/60)+2 # Just an arbitrary small increase to scan time to account for all the other bits
    print('Estimated Scan Time for {}: {} minutes'.format(scan_name, round(estimated_time, 4)))
    #input('Press Enter to continue...')

    with GCSDevice(CONTROLLERNAME) as pidevice, HH400_Histo_Manager(mode=0,send_error_email = send_email) as HH400, open(save_file, 'w') as scan_data_file:
        ########## Connect to and Initialize Piezo ##########
        pidevice.ConnectUSB(serialnum='0120036309')
        pitools.startup(pidevice, stages=STAGES, refmodes=None)
        if autozero:
            pidevice.ATZ() # autozero
            pitools.waitonautozero(pidevice)
        print('Connected to piezo stage...')
        
        ########## Prepare Scan ##########
        print('Moving to starting position...')
        #start_pos=OrderedDict([('1', xlim[0]), ('2', ylim[0]), ('3', z_focus)])
        start_pos = {'1':xlim[0],'2':ylim[0],'3':z_focus}
        pidevice.MOV(start_pos) # move to start position
        time.sleep(1.5) # wait for axes to finish motion

        ########## Begin Scan ##########
        print('Scan will begin in {} seconds...'.format(predelay))
        time.sleep(predelay) # wait before starting scan
        print('Beginning scan...')

        fig, ax1, img, axbackground = plotter(intensities, xlim, ylim, vmin, vmax)

        for i, x_pos in enumerate(xnodes):
            for j, y_pos in enumerate(ynodes):
                
                scan_time_0 = time.time() # get initial time
                
                # Move
                time_move_0 = time.time()
                pidevice.MOV({'1':x_pos,'2':y_pos}) # Move to xy position
                if (y_pos - ylim[0]) == 0: # Wait for stage in major axis case (x-axis)
                    while time.time() - time_move_0 < major_axis_wait_time:
                        pass
                else: # minor axis case (y-axis)
                    while time.time() - time_move_0 < minor_axis_wait_time:
                        pass
                
                # Get position and intensity
                real_pos = pidevice.qPOS() # get real position
                intensity_ij = HH400.poll_intensity()# measure intensity for tacq ms
                # intensity_ij = HH400.integrate_intensity(tacq=tacq, test_abscounts='{}-abscounts.txt'.format(scan_name)) # testing histogram counts vs getcountrate counts
                # intensity_ij = HH400.poll_intensity()/10

                # Store data
                intensities_split[0, i, j] = intensity_ij[0]
                intensities_split[1, i, j] = intensity_ij[1]
                intensities[i, j] = np.sum(intensity_ij)

                scan_time_f = time.time()
                scan_data_file.write("%s,%s,%s,%s,%s,%s\n" % (real_pos['1'], real_pos['2'], real_pos['3'],intensity_ij[0], intensity_ij[1], (scan_time_f - scan_time_0)))
                print('current pos: (%4.2f, %4.2f) ; Intensity: %d' % (x_pos, y_pos, (intensities[i,j])))
            img.set_data(intensities.T)
            fig.canvas.restore_region(axbackground)
            ax1.draw_artist(img)
            fig.canvas.blit(ax1.bbox)
            fig.canvas.flush_events()
            
            # TODO thread real time scan image
        
        # Return to Starting Position
        print('Done')
        pidevice.MOV({'1':xlim[0],'2': ylim[0],'3': z_focus}) # move to min position
        
    # Close Connection
    print('Closed connection to HH400 stage...')
    print('Closed connection to piezo stage...')

    # return intensities, intensities_split1, intensities_split2
    return Xs, Ys, intensities, intensities_split, estimated_time

def plotter(intensities, xlim, ylim, vmin, vmax, norm = 'linear'):
    if norm == 'log':
        norm_scale=mpl.colors.LogNorm(vmin=vmin, vmax=vmax)
    elif norm == 'linear':
        norm_scale=mpl.colors.Normalize(vmin=vmin, vmax=vmax)
    else:
        pass
        #raise Exception("Invalid norm type")

    # Initialize blitting for live plotting
    fig = plt.figure()
    ax1 = fig.add_subplot(1, 1, 1)
    img = ax1.imshow(intensities, origin='lower', norm=norm_scale, extent = (*xlim, *ylim), interpolation="None", cmap="viridis") #vmin=vmin, vmax=vmax
    ax1.set_xlim(xlim)
    ax1.set_ylim(ylim)
    ax1.set_xlabel('x (µm)')
    ax1.set_ylabel('y (µm)')
    fig.canvas.draw()   # note that the first draw comes before setting data 
    # cache the background
    axbackground = fig.canvas.copy_from_bbox(ax1.bbox)
    plt.show(block=False)

    return fig, ax1, img, axbackground

if __name__ == '__main__':
    
    # Check if File name already exists
    rel_path = r'C:\Users\spmno\OneDrive\Documents\spm\Scan\Scan Data\{}'.format(today)
    if not os.path.isdir(rel_path):
        os.mkdir(rel_path)

    save_file = "{}\{}_scan_data.txt".format(rel_path, scan_name)
    if os.path.isfile(save_file):
        raise Exception("File name already exists!")
    if ylim[1]<ylim[0] or xlim[1]<xlim[0]:
        raise Exception("Invalid scan area! Limits must be in increasing order!")
    
    # Run Scan
    t1=time.time()
    Xs, Ys, intensity, intensity_split, t_estim = run_scan(xlim, ylim, z_focus, resolution, tacq, save_file, vmin, vmax, predelay, autozero=False, send_email=send_email)
    t2=time.time()

    # Save intensities
    plot_name_root = '{}/{}'.format(rel_path, scan_name)
    spa.plot_int_heatmap(Xs, Ys, intensity, save=True, save_name='{}.png'.format(plot_name_root))
    spa.plot_int_heatmap(Xs, Ys, intensity_split[0], save=True, save_name='{}_ch1.png'.format(plot_name_root))
    spa.plot_int_heatmap(Xs, Ys, intensity_split[1], save=True, save_name='{}_ch2.png'.format(plot_name_root))

    # Print stats
    if show_scan_stats:
        print("Scan Stats:\n")
        print("Runtime: {} m".format((t2-t1)/60))
        print("Predicted Scan Time: {} m".format(t_estim))

        # tot_pos_error = np.sqrt(np.mean((Xs.flatten() - Xs.flatten()[0])**2 + (Ys.flatten() - Ys.flatten()[0])**2))
        pos_mean, pos_std = spa.pos_error_stats(Xs, Ys, resolution, xlim, ylim)

        print("Positional Error Stats:")
        # print("Total Positional Error: {} um".format(tot_pos_error))
        print("Mean Positional Error: {} um".format(pos_mean))
        print("Std Positional Error: {} um".format(pos_std))

    if intensity_histograms:
        spa.plot_channel_hists(Xs, Ys, intensity_split[0], intensity_split[1], normalize=False)

    # Send Email
    if send_email:

        message = "\n\nThe scan, '{}', has finished. The plot is attached.\n\nCordially,\nS.P. Microscope".format(scan_name)
        subject = 'SPM Scan Finished: {}'.format(scan_name)
        attachment = '{}.png'.format(plot_name_root)
        emailer.send_gmail_with_attachment(message=message, subject=subject, attachment=attachment, to_addrs=email_address)

    if show_plot:
        os.chdir(r"C:\Users\spmno\OneDrive\Documents\spm\Scan\Scan Data\\" + datetime.today().strftime('%Y-%m-%d'))
        image = Image.open('{}.png'.format(scan_name))
        image.show()

        #image1 = Image.open('{}_ch1.png'.format(scan_name))
        #image1.show()

        #image2 = Image.open('{}_ch2.png'.format(scan_name))
        #image2.show()

    sys.exit(0)