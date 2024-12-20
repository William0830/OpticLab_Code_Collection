import numpy as np
import matplotlib.pyplot as plt
import os
import scan_plot_and_analysis as spa


scan_name = r'C:\Users\spmno\OneDrive\Documents\spm\test4\Scan Data\2023-08-03\2023-08-03_MH-01-17_DropCast_34_scan_data.txt'

Xs, Ys, Ts, CH1_ints, CH2_ints = spa.load_scan_data(5, 5, .1, scan_name)


spa.plot_int_heatmap(Xs, Ys, CH1_ints, size=(8, 8), save=False, save_name='scan.png')