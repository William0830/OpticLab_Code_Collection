from pipython import GCSDevice, pitools
from collections import OrderedDict
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import time
from datetime import datetime

from hydraharp_intensities import HH400_Histo_Manager

def run_scan(start_pos, mode, increment = 0.5, tacq=100, autozero=False, focus_data_fn='focus_data', block = 6):
    """Connect, setup system and move stages and display the positions in a loop."""
    
    if mode in ['m', 'gcm', 'a', 'gca', 'ascan']:
        pass
    else:
        raise ValueError('Invalid mode: {}'.format(mode))
    # input('Press Enter to continue with focus scan...')

    # Open Connections
    CONTROLLERNAME = 'E-727'
    with GCSDevice(CONTROLLERNAME) as pidevice, HH400_Histo_Manager(send_error_email = False) as HH400, open(focus_data_fn, 'w') as focus_data_file:
        connect_piezo(pidevice, autozero=autozero)
        # Select Mode
        if mode == 'ascan':
            ascan(pidevice, HH400, focus_data_file, tacq=tacq, block=block)
        elif 'a' in mode:
            amodes(pidevice, HH400, focus_data_file, increment, start_pos, mode, tacq=tacq, block=block)
        elif 'm' in mode:
            mmodes(pidevice, HH400, focus_data_file, start_pos, mode, tacq=tacq, block=block)
        pidevice.MOV({'1': 0}) # move to min position in x (to avoid photobleaching)
    print('Closed connection to HH400 and Piezo stage...')
    print('Done')
    return None

def connect_piezo(pidevice, autozero=False):
    # Specify controller and the stages to be connected to this controller.
    STAGES = ['P-517.3CD', 'P-517.3CD', 'P-517.3CD'] # connect stages to axes
    # Connect to and Initialize Piezo
    pidevice.ConnectUSB(serialnum='0120036309')
    pitools.startup(pidevice, stages=STAGES, refmodes=None)
    if autozero:
        pidevice.ATZ() # autozero
        pitools.waitonautozero(pidevice)
    print('Connected to piezo stage...')

    return None

def single_point_plotter(mode):
        # Initialize plot for single point
        fig = plt.figure()
        ax = fig.add_subplot(111)
        Sum = ax.scatter([], [], c='b', label='Sum')
        Split1 = ax.scatter([], [], c='r', label='CH 1')
        Split2 = ax.scatter([], [], c='g', label='CH 2')
        if 'm' in mode:
            ax.set_xlabel('Time (s)')
        elif 'a' in mode:
            ax.set_xlabel('Z (µm)')
        ax.set_ylabel('Intensity (counts)')
        ax.set_title('Focus Scan')
        ax.legend((Sum, Split1, Split2), ('Sum', 'CH 1', 'CH 2') , loc='upper right')
        fig.canvas.draw()
        plt.show(block=False)
        return ax, Sum, Split1, Split2

def multipoint_plotter(xlim, ylim, pxs):
    # Initialize plotter for multiple points
    intensities = np.zeros((pxs, pxs))
    fig = plt.figure()
    ax1 = fig.add_subplot(1, 1, 1)
    norm=mpl.colors.LogNorm(vmin=50, vmax=500000)
    img = ax1.imshow(intensities, origin='lower',norm=norm, extent = (*xlim, *ylim), interpolation="None", cmap="Spectral_r")
    ax1.set_xlim(xlim)
    ax1.set_ylim(ylim)
    ax1.set_xlabel('x (µm)')
    ax1.set_ylabel('y (µm)')
    fig.canvas.draw()
    # cache the background
    axbackground = fig.canvas.copy_from_bbox(ax1.bbox)
    plt.show(block=False)

    return fig, ax1, img, axbackground

def block_query(z, zs, ts, ints, HH400, focus_data_file, t_start, mode, tacq, block):
    t_ns = []
    z_ns = []
    int_ns = [[], [], []]
    for n in range(0, block):
        if 'gc' not in mode:
            intensity_ij = HH400.integrate_intensity(tacq=tacq)
        else:
            intensity_ij = HH400.poll_intensity()

        time_n = time.time()-t_start
        int_ns[0].append(np.sum(intensity_ij))
        int_ns[1].append(intensity_ij[0])
        int_ns[2].append(intensity_ij[1])
        z_ns.append(z)
        t_ns.append(time_n)
        focus_data_file.write('{},{},{},{},{}\n'.format(z, time_n, intensity_ij[0], intensity_ij[1], int_ns[0][-1]))

    if 'm' in mode:
        ts.append(np.mean(t_ns))
    else:
        zs.append(np.mean(z_ns))

    ints[0].append(np.mean(int_ns[0]))
    ints[1].append(np.mean(int_ns[1]))
    ints[2].append(np.mean(int_ns[2]))

    return None

def scan_query(HH400, focus_data_file, intensity, i, j, t_scan):
    intensity_ij = HH400.poll_intensity()
    intensity[i, j, 0] = np.sum(intensity_ij)
    intensity[i, j, 1] = intensity_ij[0]
    intensity[i, j, 2] = intensity_ij[1]
    # Writes for each point (i, j) for t_scan: "scan_time, intensity_sum, intensity_ch1, intensity_ch2, intensity_sum"
    focus_data_file.write('{},{},{},{}\n'.format(t_scan, intensity[i, j, 0], intensity[i, j, 1], intensity[i, j, 2]))


def amodes(pidevice, HH400, focus_data_file, increment, start_pos, mode, tacq, block):

    # Initialize position
    print('Moving to ({}, {}, {})...'.format(start_pos['1'], start_pos['2'], start_pos['3']))
    pidevice.MOV(start_pos) # move to min position
    time.sleep(1) # wait for axes to finish motion
    z = pidevice.qPOS()['3'] # get current position

    # Initialize Plotting
    ax, Sum, Split1, Split2 = single_point_plotter(mode)
    ax.set_xlim([z, 21])

    # initialize data storing arrays
    ints = [[], [], []] # initialize array of intensities
    zs = [] # initialize array of z positions
    ts = []
    
    t_start = time.time()
    _move_time = 0.20 # seconds
    count = 0
    while True:

        block_query(z, zs, ts, ints, HH400, focus_data_file, t_start, mode, tacq, block)

        z += increment
        if z > 20:
            break
        else:
            pidevice.MOV({'3': z}) # move to next position
            time_i = time.time()
        
        # Update Intensities Plot
        if count >= 400: # only plot last 400 points
            count  = 400
        ax.clear()

        ax.scatter(zs[-count:], ints[0][-count:], c='b')
        ax.scatter(zs[-count:], ints[1][-count:], c='r')
        ax.scatter(zs[-count:], ints[2][-count:], c='g')
        ax.legend((Sum, Split1, Split2), ('Sum', 'CH 1', 'CH 2') , loc='upper right')
        plt.pause(0.001)

        while time.time() - time_i < _move_time:
                pass
        count += 1
    
    # Print max intensity positions (Sum, CH1, CH2)
    ind = ints[0].index(max(ints[0]))
    ind1 = ints[1].index(max(ints[1]))
    ind2 = ints[2].index(max(ints[2]))
    print('Max intensity z positions (Sum, CH1, CH2): %f, %f, %f' % (zs[ind], zs[ind1], zs[ind2]))
    
def mmodes(pidevice, HH400, focus_data_file, start_pos, mode, tacq, block):
    
    # Initialize position
    mmode_start_pos = {'1': start_pos['1'], '2': start_pos['2'], '3': 10}
    print('Moving to ({}, {}, {})...'.format(start_pos['1'], start_pos['2'], 10))
    pidevice.MOV(mmode_start_pos)
    time.sleep(1)
    z = pidevice.qPOS()['3']

    # Initialize plotting
    pidevice.MOV({'3': 10}) # move to min position
    ax, Sum, Split1, Split2 = single_point_plotter(mode)

    # initialize data storing arrays
    ints = [[], [], []] # initialize array of intensities
    ts = []
    zs = [] # initialize array of z positions

    t_start = time.time()
    count = 0
    while True:
        
        block_query(z, zs, ts, ints, HH400, focus_data_file, t_start, mode, tacq, block)

        # Update Intensities Plot
        prev_t = ts[-1]
        if count >= 50: # only plot last 400 points
            count  = 50
        ax.clear()

        ax.set_xlim([prev_t-18, prev_t + 5])
        ax.scatter(ts[-count:], ints[0][-count:], c='b')
        ax.scatter(ts[-count:], ints[1][-count:], c='r')
        ax.scatter(ts[-count:], ints[2][-count:], c='g')
        ax.legend((Sum, Split1, Split2), ('Sum', 'CH 1', 'CH 2') , loc='upper right')
        plt.pause(0.001)
        count += 1

def ascan(pidevice, HH400, focus_data_file, tacq=100, block = None):
    _major_move = 0.3 # seconds
    _minor_move = 0.13 # seconds
    _xlim = [30, 60]
    _ylim = [30, 60]
    _pxs = 15
    xnodes = np.linspace(_xlim[0], _xlim[1], _pxs)
    ynodes = np.linspace(_ylim[0], _ylim[1], _pxs)

    # Initialize scanning position
    pidevice.MOV({'1': xnodes[0], '2': ynodes[0], '3': 10}) # move to min position
    time.sleep(1) # wait for axes to finish motion

    # Initialize plotting
    fig, ax1, img, axbackground = multipoint_plotter(_xlim, _ylim, _pxs)

    # initialize data storing arrays
    t_start = time.time()
    
    while True:
        t_scan = time.time() - t_start
        intensity = np.zeros((_pxs, _pxs, 3))
        for i, x_pos in enumerate(xnodes):
            for j, y_pos in enumerate(ynodes):
                time_move_0 = time.time()
                pidevice.MOV(OrderedDict([('1', x_pos), ('2', y_pos)])) # Move to xy position
                if (y_pos - _ylim[0]) == 0: # Wait for stage in major axis case (x-axis)
                    while time.time() - time_move_0 < _major_move:
                        pass
                else: # minor axis case (y-axis)
                    while time.time() - time_move_0 < _minor_move:
                        pass
                pidevice.MOV({'1': x_pos, '2': y_pos})

                scan_query(HH400, focus_data_file, intensity, i, j, t_scan)
                print('Scanning ({}, {})...'.format(x_pos, y_pos))

        # Update Intensities Plot
        img.set_data(intensity[0].T)
        fig.canvas.restore_region(axbackground)
        ax1.draw_artist(img)
        fig.canvas.blit(ax1.bbox)
        fig.canvas.flush_events()

    return None