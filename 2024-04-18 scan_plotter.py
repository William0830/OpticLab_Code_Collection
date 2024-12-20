import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from mpl_toolkits.axes_grid1 import make_axes_locatable
import os
import scan_plot_and_analysis2 as spa


# def plot_int_heatmap(Xs, Ys, channel_ints, size=(8, 8), save=False, save_name='scan.png'):


#     """Plot intensity heatmap of 2D scan."""
    
#     Z = channel_ints

#     axis_label_size = 26
#     axis_tick_size = 22
#     cb_label_size = 26
#     cb_tick_size = 16
    
#     fig, ax = plt.subplots(1, 1, figsize=size)

#     plot = ax.pcolor(Xs, Ys, Z, cmap='viridis', shading='auto', norm=colors.LogNorm(vmin=Z.min(), vmax=Z.max()))
#     ax.set_aspect('equal')

#     divider = make_axes_locatable(ax)
#     cax = divider.append_axes("right", size="5%", pad=0.10)
#     cb = plt.colorbar(plot, cax=cax, orientation='vertical')
#     cb.ax.tick_params(labelsize=cb_tick_size)
#     cb.set_label(label='Intensity (counts/100ms)', fontsize=cb_label_size)
    
#     # ax.autoscale(tight=True)
#     ax.set_xlabel('X (µm)', fontsize=axis_label_size)
#     ax.set_ylabel('Y (µm)', fontsize=axis_label_size)
#     ax.tick_params(axis='both', which='major', labelsize=axis_tick_size)
#     # ax.set_title(title, fontsize=26, pad=20)
#     plt.tight_layout()

#     if save:
#         plt.savefig(save_name, dpi=300)
#         plt.close(fig)
#     else:
#         plt.show()

#read in abscounts
scan_name = r"C:\Users\spmno\OneDrive\Documents\spm\Scan\Scan Data\2024-12-20/2024-12-20_pq3_scan_data.txt"
scan_name2=r"C:\Users\spmno\OneDrive\Documents\spm\Scan\Scan Data\2024-10-15/2024-10-15_pq10_scan_data.txt"

corr=0

length = 10
res = .5

Xs, Ys, Ts, CH1_ints, CH2_ints = spa.load_scan_data(length, length, res, scan_name)
# Xs2,Ys2,Ts2, CH1_ints2, CH2_ints2 = spa.load_scan_data(length, length, res, scan_name2)
sumed = CH1_ints + CH2_ints
#sumed2=CH1_ints2+CH2_ints2

print("Sum Max: " + str(np.max(sumed)),"Ch.1 Max: " + str(np.max(CH1_ints)), "Ch.2 Max: " + str(np.max(CH2_ints)))
print("Sum Min: " + str(np.min(sumed)),"Ch.1 Min: " + str(np.min(CH1_ints)), "Ch.2 Min: " + str(np.min(CH2_ints)))


c1norm=CH1_ints/np.max(CH1_ints)
c2norm=CH2_ints/np.max(CH2_ints)

sub=c1norm-c2norm

# for i in range(len(sumed)): 
#     for j in range(len(sumed)):
#         if sumed[i][j]>150000:
#             sumed[i][j]=0
# plt.figure(figsize=(4,4))
# plt.hist(sub, bins=1000)
# plt.xlabel("Intensity (counts/s)",size=13)
# plt.ylabel("Frequency",size=13)
# plt.tick_params(axis='both',  labelsize=10)

test=np.ma.masked_greater(sumed,10000)

if corr!=1:

    spa.plot_int_heatmap(Xs, Ys,sumed, save=False)
    # spa.plot_channel_hists(Xs, Ys, CH1_ints, CH2_ints, normalize=False)
    # spa.plot_int_heatmap(Xs, Ys, sumed, save=False)
    # spa.plot_positions_and_error(Xs,Ys,res,xlim=(82,84),ylim=(79,81))
    plt.show()

#### IF YOU WANT CORRELATED IMAGES ALREADY, THEN USE THIS: 

if corr==1: 
   flip=np.flip(sumed,axis=0)
   Xs_flip=np.flip(Xs,axis=0)  
   spa.plot_int_heatmap(-Xs_flip, Ys, flip, save=False)
   plt.show()

