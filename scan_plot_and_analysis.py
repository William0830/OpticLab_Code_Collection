import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
import warnings
import diptest

warnings.filterwarnings('ignore')

def load_scan_data(distx, disty, res, scan_data_file):
    # Read in data from 2D scan return files
    lenx = int(distx / res) + 1
    leny = int(disty / res) + 1

    (xs, ys, zs, ch1_ints, ch2_ints, ts) = np.loadtxt(scan_data_file, dtype = float, delimiter=',', unpack=True)

    Xs = np.reshape(xs, (lenx, leny))
    Ys = np.reshape(ys, (lenx, leny))
    Ts = np.reshape(ts, (lenx, leny))
    CH1_ints = np.reshape(ch1_ints, (lenx, leny))
    CH2_ints = np.reshape(ch2_ints, (lenx, leny))

    return Xs, Ys, Ts, CH1_ints, CH2_ints

def plot_int_heatmap(Xs, Ys, channel_ints, size=(8, 8), save=False, save_name='scan.png', vmin=None, vmax=None):
    """Plot intensity heatmap of 2D scan."""

    axis_label_size = 26
    axis_tick_size = 22
    cb_label_size = 26
    cb_tick_size = 16
    
    fig, ax = plt.subplots(1, 1, figsize=size)

    plot = ax.pcolor(Xs, Ys, channel_ints, cmap='viridis', shading='auto', vmin=vmin, vmax=vmin)
    ax.set_aspect('equal')

    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.10)
    cb = plt.colorbar(plot, cax=cax, orientation='vertical')
    cb.ax.tick_params(labelsize=cb_tick_size)
    cb.set_label(label='Intensity (counts/100ms)', fontsize=cb_label_size)
    
    # ax.autoscale(tight=True)
    ax.set_xlabel('X (µm)', fontsize=axis_label_size)
    ax.set_ylabel('Y (µm)', fontsize=axis_label_size)
    ax.tick_params(axis='both', which='major', labelsize=axis_tick_size)
    # ax.set_title(title, fontsize=26, pad=20)
    plt.tight_layout()

    if save:
        plt.savefig(save_name, dpi=300)
        plt.close(fig)
    else:
        plt.show()

def plot_positions_and_error(Xs,Ys, res, xlim = (0, 100), ylim = (0, 100), ticks = 2):
    # Xs and Ys are Meshgrids; res is float; xlim and ylim are length 2 tuples
    # ticks is an int describing relative number of ticks per resolution unit

    xnodes = np.linspace(xlim[0], xlim[1], int((xlim[1]-xlim[0])/res) + 1).round(decimals=3) # x coordinates [0, distx] (um)
    ynodes = np.linspace(ylim[0], ylim[1], int((ylim[1]-ylim[0])/res) + 1).round(decimals=3)

    Xs_ideal, Ys_ideal = np.meshgrid(xnodes, ynodes, indexing='ij')

    Xs_error = Xs_ideal - Xs
    Ys_error = Ys_ideal - Ys
    total_error = np.sqrt(np.square(Xs_error) + np.square(Ys_error))

    fig, ax = plt.subplots(1, 2, figsize=(10, 5))
    ax[0].scatter(Xs, Ys, marker='o')
    ax[0].set_xticks(np.arange(xlim[0], xlim[1] + ticks*res, ticks*res))
    ax[0].set_yticks(np.arange(ylim[0], ylim[1] + ticks*res, ticks*res))
    ax[0].set_xlabel('X (µm)')
    ax[0].set_ylabel('Y (µm)')
    ax[0].grid(True, which='both')
    ax[0].set_title('Piezo Position On Grid (µm)')

    plot = ax[1].pcolor(Xs, Ys, total_error, cmap='Spectral', shading='auto')
    ax[1].set_xlabel('X (µm)')
    ax[1].set_ylabel('Y (µm)')
    ax[1].set_title('Total Positional Error (µm)')
    # ax[1].set_aspect('equal')
    plt.colorbar(plot, ax=ax[1], label=r'$\sqrt{(X_{ideal} - X_{exp})^2 + (Y_{ideal} - Y_{exp})^2}$' + ' (µm)')
    plt.tight_layout()
    plt.show()

    return None

def plot_timespent(Xs, Ys, Ts):
    # Xs, Ys, and ideal positions are all Meshgrids
    fig, ax = plt.subplots(1, 2, figsize=(10, 5))

    heatmap_time = ax[0].pcolormesh(Xs, Ys, Ts, cmap='coolwarm')
    plt.colorbar(heatmap_time, ax=ax[0])
    ax[0].set_xlabel('x (µm)')
    ax[0].set_ylabel('y (µm)')
    ax[0].set_title('Time Spent at Each Grid Point heatmap')

    ax[1].hist(Ts.flatten(), bins=50)
    ax[1].set_xlabel('Time (s)')
    ax[1].set_ylabel('Counts')
    ax[1].set_title('Time Spent at Points Distribution')
    plt.tight_layout()
    plt.show()

def pos_error_stats(Xs, Ys, res, xlim, ylim):
    xnodes = np.linspace(xlim[0], xlim[1], int((xlim[1]-xlim[0])/res) + 1).round(decimals=3)
    ynodes = np.linspace(ylim[0], ylim[1], int((ylim[1]-ylim[0])/res) + 1).round(decimals=3)
    print(len(xnodes), len(ynodes))
    Xs_ideal, Ys_ideal = np.meshgrid(xnodes, ynodes, indexing='ij')

    X_err = Xs_ideal - Xs
    Y_err = Ys_ideal - Ys

    combined_errors = np.array([X_err, Y_err]).flatten()

    mean = np.mean(combined_errors)
    stdev = np.std(combined_errors)

    return mean, stdev



def plot_channel_hists(Xs, Ys, Ch1_ints, Ch2_ints, normalize=False):

    fig, ax = plt.subplots(1,2,figsize=(10,5))

    if not normalize:
        ax[0].hist(Ch1_ints.flatten(), bins=50, alpha=0.5,  density=True, label='Ch1')
        ax[0].hist(Ch2_ints.flatten(), bins=50, alpha=0.5,  density=True ,label='Ch2')
        ax[0].set_xlabel('Pixel Intensity (photons/100ms)')
        ax[0].set_title('Absolute Channel Int Hists')
    else:
        norm_ch = lambda x: x/np.max(x)
        norm_ch1 = norm_ch(Ch1_ints)
        norm_ch2 = norm_ch(Ch2_ints)

        ax[0].hist(norm_ch1.flatten(), bins=50, alpha=0.5,  density=True, label='Ch1')
        ax[0].hist(norm_ch2.flatten(), bins=50, alpha=0.5,  density=True ,label='Ch2')
        ax[0].set_xlabel('Normed Pixel Intensity (normed photons/100ms)')
        ax[0].set_title('Norm Channel Int Hists')
    ax[0].legend()
    ax[0].set_ylabel('Counts')

    channel_dif_ints = Ch2_ints - Ch1_ints
    sigma = np.std(channel_dif_ints)
    xbar = np.mean(channel_dif_ints)

    ax[1].hist(channel_dif_ints.flatten(), bins=50, density=True)
    ax[1].text(0.7, 0.8, r"$\sigma =$ {}".format(round(sigma, 2)), transform = ax[1].transAxes)
    ax[1].text(0.7, 0.7, r"$\mu =$ {}".format(round(xbar, 2)), transform = ax[1].transAxes)
    ax[1].set_xlabel(r'Abs pixel Int diff $(Ch1_{ij} - Ch2_{ij})$')
    ax[1].set_title('Differential Channel Int Hist: ')
    ax[1].set_ylabel('Counts')

    plt.show()

def hartigans_diptest(data):
    # https://gist.github.com/larsmans/3153330
    # https://stackoverflow.com/questions/38420847/how-to-test-if-a-distribution-is-unimodal-or-not-in-python
    #
    # Hartigan's dip test for unimodality / multimodality.
    # This tests the null hypothesis that the data are unimodal.
    # Parameters
    # ----------
    # data : ndarray
    #     One-dimensional array of data, of length n.
    # Returns
    # -------
    # p : float
    #     The p-value, interpreted as follows:
    #     p > 0.1: data are likely unimodal
    #     p <= 0.1: data are likely multimodal
    # References
    # ----------
    # Hartigan, J. A.; Hartigan, P. M. (1985), "The Dip Test of Unimodality", The Annals of Statistics 13 (1): 70–84, doi:10.1214/aos/1176346577, JSTOR 2240974.
    # Examples
    # --------

    return diptest.diptest(data)

