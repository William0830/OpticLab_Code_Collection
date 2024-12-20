import numpy as np
from io import BytesIO
import matplotlib.pyplot as plt
import os

os.chdir(r"C:\Users\spmno\OneDrive\Documents\spm\Intensity Traces\2024-08-27\2024-08-27 Dot1 T2 15min.g2.run")
importt2 = 1
normalize = 0
# Import t2 data        
data = np.genfromtxt('g2', delimiter = ",")

if importt2 == 1:
    x=data[data[:,1]>data[:,0],:][:,[2,4]][:,0]
    y=data[data[:,1]>data[:,0],:][:,[2,4]][:,1]

# =============================================================================
#     x = []
#     y = []
#     for i in range(len(data)):
#         if data[i][1] > data[i][0]:
#             y = np.append(y, data[i][-1])
#             x = np.append(x, data[i][2]) # Take middle of bin for time
# 
# 
# ============================================================================# Normalize to background
if normalize == 1:
    bgarray = np.append(y[0:len(y)//2 - 3000], y[len(y)//2 + 3000:-1])
    bg = np.mean(bgarray)
    #y = y/bg
    y=y/np.mean(y)

def timescale(time):
    
    '''Scale binned data to the appropriate SI prefix for time'''
    timetag = "ps"
    divby = 1
    endtime = time[-1] # Define endtime as the last entry in the array
    if 10**3 <= endtime <= 10**5:
        timetag = "ns"
        divby = 10**3
    elif 10**5 <= endtime <= 10**8:
        timetag = "us"
        divby = 10**6
    elif 10**8 <= endtime <= 10**12:
        timetag = "ms"
        divby = 10**9
    elif 10**12 <= endtime:
        timetag = "s"
        divby = 10**12
    time =  time/divby
    return time, timetag

x, timetag = timescale(x)
#x = x*10**3 #Convert to ns  

# =============================================================================
# # Plot to check
# fig, ax = plt.subplots(figsize=(8,8))
# ax.plot(x,y,alpha=.7)
# plt.axis([-200,200,0,1.3])
# plt.xlabel("Time $(ns)$",size=26)
# plt.ylabel("Correlation Counts (norm.)",size=26)
# plt.tick_params(axis='both', labelsize=22)
# ax.axhline(y=.5,ls='-.',lw=3,color='red')
# plt.annotate(r'$g^2$$($$\tau$$)$$=0.5$',(80,0.51),size=22)
# fig.show()
# 
# =============================================================================
fig, ax = plt.subplots(figsize=(4,4))
ax.scatter(x,y,alpha=.8,color='black',s=10)
#plt.axis([-100,100,0,1.3])
plt.xlabel("Time (ns)",size=14)
plt.ylabel(r'$\mathrm{g^{2}(\tau)}$ (norm.)',size=14,labelpad=-1)
#plt.yticks([0,0.5,1])
plt.tick_params(axis='both', labelsize=14)
#ax.axhline(y=.5,ls='-.',lw=3,color='grey')
#plt.annotate(r'$\mathrm{g^{2}(0)=0.25}$',(-35,0.1),size=13)
#plt.text(-97,1.20,"c",size=18)
#plt.subplots_adjust(top=.96,bottom=.170,left=.200,right=.945,hspace=0,wspace=0)
#ax.axis([-200,200,0.,1.5])
plt.tight_layout()
plt.show()
#plt.savefig("g2 zoom.png",dpi=600)
