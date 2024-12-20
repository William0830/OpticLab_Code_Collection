from pipython import GCSDevice, pitools
from collections import OrderedDict
import matplotlib.pyplot as plt
import numpy as np
import time
import sys
import os
from PIL import Image
from datetime import datetime

from hydraharp_intensities2 import HH400_Histo_Manager
import scan_plot_and_analysis as spa
import auto_emailer as emailer

# Test parameters
# z_focus = 3.062 # µm

z_foci = np.linspace(0,6,9)
run_number = 1
xlim = (55, 57) # µm
ylim = (56.5,58.5) # µm
resolution = .05 # um
# vmin = 100000
# vmax = 400000

tacq = 100 # ms
experiment_titles = ['pq{}_z{}'.format(run_number, round(i, 3)) for i in z_foci]
email_address = 'spmnotif@gmail.com'
send_email = 0
predelay = 0 # s
show_plot = False
intensity_histograms=False
show_scan_stats = False


# naming convention
today = datetime.today().strftime('%Y-%m-%d')
scan_names = ['{}_{}'.format(today, experiment_title) for experiment_title in experiment_titles]

# Specify controller and the stages to be connected to this controller.
CONTROLLERNAME = 'E-727'
STAGES = ['P-517.3CD', 'P-517.3CD', 'P-517.3CD'] # connect stages to axes

def run_scan(xlim, ylim, z_focus, resolution, tacq, save_file, predelay=0, autozero=False, send_email=False):
    """Connect, setup system and move stages and display the positions in a loop."""

    major_axis_wait_time = 0.20 # seconds
    minor_axis_wait_time = 0.10 # seconds
    
    # scan points in x and y [x0, xf] x [y0, yf] (um); z is fixed;
    xnodes = np.linspace(xlim[0], xlim[1], int((xlim[1]-xlim[0])/resolution) + 1).round(decimals=3) # x coordinates [0, distx] (um)
    ynodes = np.linspace(ylim[0], ylim[1], int((ylim[1]-ylim[0])/resolution) + 1).round(decimals=3)

    Xs, Ys = np.meshgrid(xnodes, ynodes, indexing='ij')

    len_x = len(xnodes)
    len_y = len(ynodes)

    xtime = (len_x - 1) * (major_axis_wait_time + tacq/1000 + 0.05)
    ytime = (len_x - 1) * len_y * (major_axis_wait_time + tacq/1000 + 0.05) + minor_axis_wait_time + tacq/1000

    # estimated_time = 1/60 * (xtime + ytime + predelay + 2.4) #Deprecated since 2024-07-23
    estimated_time = ((((xlim[1] - xlim[0])/resolution) * ((ylim[1] - ylim[0])/resolution))*.1/60)+2 # Just an arbitrary small increase to scan time to account for all the other bits

    print('Estimated Scan Time for {}: {} minutes'.format(scan_name, estimated_time))
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
        start_pos = OrderedDict([('1', xlim[0]), ('2', ylim[0]), ('3', z_focus)])
        pidevice.MOV(start_pos) # move to min position
        time.sleep(1) # wait for axes to finish motion

        ########## Begin Scan ##########
        # print('Scan will begin in {} seconds...'.format(predelay))
        print('Beginning scan...')

        
        intensities = np.zeros((len_x, len_y)) # initialize array of intensities
        intensities_split = np.zeros((2, len_x, len_y))

        for i, x_pos in enumerate(xnodes):
            for j, y_pos in enumerate(ynodes):
                
                scan_time_0 = time.time() # get initial time
                
                # Move
                time_move_0 = time.time()
                pidevice.MOV(OrderedDict([('1', x_pos), ('2', y_pos)])) # Move to xy position
                if (y_pos - ylim[0]) == 0: # Wait for stage in major axis case (x-axis)
                    while time.time() - time_move_0 < major_axis_wait_time:
                        pass
                else: # minor axis case (y-axis)
                    while time.time() - time_move_0 < minor_axis_wait_time:
                        pass
                
                # Get position and intensity
                real_pos = pidevice.qPOS() # get real position
                intensity_ij = HH400.poll_intensity() # measure intensity for tacq ms
                # intensity_ij = HH400.integrate_intensity(tacq=tacq, test_abscounts='{}-abscounts.txt'.format(scan_name)) # testing histogram counts vs getcountrate counts

                # Store data
                intensities_split[0, i, j] = intensity_ij[0]
                intensities_split[1, i, j] = intensity_ij[1]
                intensities[i, j] = np.sum(intensity_ij)

                scan_time_f = time.time()
                scan_data_file.write("%s,%s,%s,%s,%s,%s\n" % (real_pos['1'], real_pos['2'], real_pos['3'],intensity_ij[0], intensity_ij[1], (scan_time_f - scan_time_0)))
                print('current pos: (%4.2f, %4.2f) ; Intensity: %d' % (x_pos, y_pos, np.sum(intensity_ij)))
            
            # TODO thread real time scan image
            # plt.pcolormesh(Xs,Ys, intensities)
            # plt.pause(0.001)
        
        # Return to Starting Position
        print('Done')
        pidevice.MOV(start_pos) # move to min position
        
    # Close Connection
    print('Closed connection to HH400 stage...')
    print('Closed connection to piezo stage...')

    # return intensities, intensities_split1, intensities_split2
    return Xs, Ys, intensities, intensities_split

if __name__ == '__main__':
    
    # Check if File name already exists
    rel_path = r'C:\Users\spmno\OneDrive\Documents\spm\Scan\Scan Data\{}\focus_data_pq'.format(today)
    if not os.path.isdir(rel_path):
        os.mkdir(rel_path)

    for i in range(len(scan_names)):
        scan_name = scan_names[i]
        z_focus = z_foci[i]

        save_file = "{}\{}_scan_data.txt".format(rel_path, scan_name)
        if os.path.isfile(save_file):
            raise Exception("File name already exists!")
        
        # Run Scan
        time.sleep(predelay) # wait before starting scan
        t1=time.time()
        Xs, Ys, intensity, intensity_split = run_scan(xlim, ylim, z_focus, resolution, tacq, save_file, predelay, autozero=False, send_email=send_email)
        t2=time.time()

        # Save intensities
        plot_name_root = '{}/{}'.format(rel_path, scan_name)
        spa.plot_int_heatmap(Xs, Ys, intensity, save=True, save_name='{}.png'.format(plot_name_root)) #vmin=vmin, vmax=vmax
        spa.plot_int_heatmap(Xs, Ys, intensity_split[0], save=True, save_name='{}_ch1.png'.format(plot_name_root))
        spa.plot_int_heatmap(Xs, Ys, intensity_split[1], save=True, save_name='{}_ch2.png'.format(plot_name_root))

        # Print stats
        if show_scan_stats:
            print("Scan Stats:\n")
            print("Runtime: {} s".format(t2-t1))
            print("Predicted Scan Time: {} s".format(tacq/1000*len(Xs)*len(Ys) + 0.05*len(Xs)*(len(Ys)-1) + 0.1*len(Ys)*(len(Ys)-1) + predelay + 2.4 + 0.2*len(Xs)*(len(Xs)-1) + 0.1*len(Ys)*(len(Ys)-1) + 0.5))

            tot_pos_error = np.sqrt(np.mean((Xs.flatten() - Xs.flatten()[0])**2 + (Ys.flatten() - Ys.flatten()[0])**2))
            pos_mean, pos_std = spa.pos_error_stats(Xs, Ys, resolution, xlim, ylim)

            print("Positional Error Stats:")
            print("Total Positional Error: {} um".format(tot_pos_error))
            print("Mean Positional Error: {} um".format(pos_mean))
            print("Std Positional Error: {} um".format(pos_std))

            # hartigan's dip test for unimodality
            # https://gist.github.com/larsmans/3153330
            # https://stackoverflow.com/questions/38420847/how-to-test-if-a-distribution-is-unimodal-or-not-in-python

            ch1_unimodality = spa.hartigans_diptest(intensity_split[0].flatten())
            ch2_unimodality = spa.hartigans_diptest(intensity_split[1].flatten())
            combined_unimodality = spa.hartigans_diptest(intensity.flatten())
            differential_unimodality = spa.hartigans_diptest((intensity_split[0] - intensity_split[1]).flatten())

            print("Intensity Stats:")
            print("Ch1 Unimodality: {}, p score: {}".format(ch1_unimodality[0], ch1_unimodality[1]))
            print("Ch2 Unimodality: {}, p score: {}".format(ch2_unimodality[0], ch2_unimodality[1]))
            print("Combined Channel Unimodality: {}, p score: {}".format(combined_unimodality[0], combined_unimodality[1]))
            print("Differential Unimodality: {}, p score: {}".format(differential_unimodality[0], differential_unimodality[1]))

        if intensity_histograms:
            spa.plot_channel_hists(Xs, Ys, intensity_split[0], intensity_split[1], normalize=False)

        # Send Email
        if send_email:

            message = "\n\nThe scan, '{}', has finished. The plot is attached.\n\nCordially,\nS.P. Microscope".format(scan_name)
            subject = 'SPM Scan Finished: {}'.format(scan_name)
            attachment = '{}.png'.format(plot_name_root)
            emailer.send_gmail_with_attachment(message=message, subject=subject, attachment=attachment, to_addrs=email_address)

        if show_plot:
            image=Image.open('{}.png'.format(scan_name))
            image.show()

            image1=Image.open('{}_ch1.png'.format(scan_name))
            image1.show()

            image2 = Image.open('{}_ch2.png'.format(scan_name))
            image2.show()

sys.exit(0)