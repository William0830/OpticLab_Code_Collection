import time
import ctypes as ct
from ctypes import byref
import os
import sys
import numpy as np

import auto_emailer as emailer

# works for python 3 and windows and linux 64 bit


class HH400_Histo_Manager:

    def __init__(self, mode,send_error_email = False):
    
        self.send_email = send_error_email

        ##### Measurement Parameters #####

        # Exp Parameters
        self.mode=mode # Choice of: 0, 2, 3 for hist, T2, T3
        self.binning            = 4 # You can change this
        self.offset             = 0
        self.syncDivider        = 1 # You can change this 
        self.syncCFDZeroCross   = 10 # You can change this (in mV)
        self.syncCFDLevel       = 50 # You can change this (in mV)
        self.syncChannelOffset  = -5000 # You can change this (in ps, like a cable delay)
        self.inputCFDZeroCross  = 10 # You can change this (in mV)
        self.inputCFDLevel      = 50 # You can change this (in mV)
        self.inputChannelOffset = 0 # You can change this (in ps, like a cable delay)
        
        # From hhdefin.h
        self.LIB_VERSION   = "3.0"
        self.MAXDEVNUM     = 8
        self.MODE_HIST     = 0
        self.MAXLENCODE    = 6
        self.HHMAXINPCHAN  = 8
        self.MODE_T2       = 2
        self.MODE_T3       = 3
        self.MAXHISTLEN    = 65536
        self.FLAG_OVERFLOW = 0x001
        self.TTREADMAX     = 131072
        self.FLAG_FIFOFULL = 0x0002

        ###### DLL buffers ######
        # Variables to store information read from DLLs
        self.counts       = [(ct.c_uint * self.MAXHISTLEN)() for i in range(0, self.HHMAXINPCHAN)]
        self.dev          = []
        self.libVersion   = ct.create_string_buffer(b"", 8) # mutable white character memory block
        self.hwSerial     = ct.create_string_buffer(b"", 8)
        self.hwPartno     = ct.create_string_buffer(b"", 8)
        self.hwVersion    = ct.create_string_buffer(b"", 8)
        self.hwModel      = ct.create_string_buffer(b"", 16)
        self.errorString  = ct.create_string_buffer(b"", 40)
        self.numChannels  = ct.c_int()
        self.histLen      = ct.c_int() # number of histogram bins should be 65536
        self.resolution   = ct.c_double()
        self.syncRate     = ct.c_int()
        self.countRate    = ct.c_int()
        self.flags        = ct.c_int()
        self.nRecords     = ct.c_int()
        self.ctcstatus    = ct.c_int()
        self.warnings     = ct.c_int()
        self.warningstext = ct.create_string_buffer(b"", 16384)
        self.buffer       = (ct.c_uint * self.TTREADMAX)()

        self.choose_DLL()
        if self.mode == 0: 
            self.mode= self.MODE_HIST
        elif self.mode == 2:   
            self.mode= self.MODE_T2
        elif self.mode == 3:   
            self.mode= self.MODE_T3
            
    def closeDevices(self):
        for i in range(0, self.MAXDEVNUM): # try to close all possible devices (even if not open)
            hhlib.HH_CloseDevice(ct.c_int(i))
        #sys.exit(0)
        return None
    
    def tryfunc(self, retcode, funcName, measRunning=False): # Function to check return values of HHLib functions and close devices if there is an error
        if retcode < 0:
            hhlib.HH_GetErrorString(self.errorString, ct.c_int(retcode))
            print("HH_%s error %d (%s). Aborted." % (funcName, retcode, self.errorString.value.decode("utf-8")))
            self.__exit__()

            # Send error email
            if self.send_email:
                message = 'HH_%s error %d (%s). Aborted.' % (funcName, retcode, self.errorString.value.decode("utf-8"))
                subject = 'Scan Aborted Because of HH400 Error'
                addr = 'minhal@uchicago.edu'
                emailer.send_email(subject=subject, message=message, to_addrs=addr)

            exit()

    def choose_DLL(self):
        global hhlib
        if os.name == "nt": # if running windows
            hhlib = ct.WinDLL("hhlib64.dll")
        else: # if running linux
            hhlib = ct.CDLL("libhh400.so")
        
        hhlib.HH_GetLibraryVersion(self.libVersion)
        # print("Library version is %s" % libVersion.value.decode("utf-8"))
        if self.libVersion.value.decode("utf-8") != self.LIB_VERSION:
            print("Warning: The application was built for version %s" % self.LIB_VERSION)
        
        return None
    
    def connect_device(self):
        for i in range(0, self.MAXDEVNUM):
            # device ID in 1-8
            retcode = hhlib.HH_OpenDevice(ct.c_int(i), self.hwSerial) # try to open device
            if retcode == 0:
                self.dev.append(i) # keep index to devices we want to use

            else:
                if retcode == -1: # HH_ERROR_DEVICE_OPEN_FAIL
                    pass
                else:
                    hhlib.HH_GetErrorString(self.errorString, ct.c_int(retcode))
                    print("  %1d        %s" % (i, self.errorString.value.decode("utf8"))) # error
        if len(self.dev) < 1: # if no devices returned end
            print("No PicoQuant device Found.")
            self.__exit__()
        # Continue with first device only
        print("\nConnected to device #%1d" % self.dev[0])
    
    def prep_measurements(self):

        ###### initialize device ######

        # Histo mode with internal clock - perhaps change to cont mode (8)
        self.tryfunc(hhlib.HH_Initialize(ct.c_int(self.dev[0]), ct.c_int(self.mode), ct.c_int(0)), "Initialize") # 0 = internal clock, 1 = external clock
        self.tryfunc(hhlib.HH_GetNumOfInputChannels(ct.c_int(self.dev[0]), byref(self.numChannels)), "GetNumOfInputChannels")    
        self.tryfunc(hhlib.HH_Calibrate(ct.c_int(self.dev[0])), "Calibrate")
        self.tryfunc(hhlib.HH_SetSyncDiv(ct.c_int(self.dev[0]), ct.c_int(self.syncDivider)), "SetSyncDiv")
        self.tryfunc(hhlib.HH_SetSyncCFD(ct.c_int(self.dev[0]), ct.c_int(self.syncCFDLevel), ct.c_int(self.syncCFDZeroCross)),"SetSyncCFD")
        self.tryfunc(hhlib.HH_SetSyncChannelOffset(ct.c_int(self.dev[0]), ct.c_int(self.syncChannelOffset)), "SetSyncChannelOffset")

        # We use the same input settings for all channels, you can change this
        for i in range(0, self.numChannels.value):
            # set constant fractional discriminator (CFD) level and zero cross
            self.tryfunc(hhlib.HH_SetInputCFD(ct.c_int(self.dev[0]), ct.c_int(i), ct.c_int(self.inputCFDLevel), ct.c_int(self.inputCFDZeroCross)), "SetInputCFD")
            self.tryfunc(hhlib.HH_SetInputChannelOffset(ct.c_int(self.dev[0]), ct.c_int(i), ct.c_int(self.inputChannelOffset)), "SetInputChannelOffset")
        
        if self.mode==3:
            self.tryfunc(hhlib.HH_SetBinning(ct.c_int(self.dev[0]), ct.c_int(self.binning)), "SetBinning") # Takes an into [0,16] power of bin width
            self.tryfunc(hhlib.HH_SetOffset(ct.c_int(self.dev[0]), ct.c_int(self.offset)), "SetOffset")
            self.tryfunc(hhlib.HH_GetResolution(ct.c_int(self.dev[0]), byref(self.resolution)), "GetResolution")
        
        if self.mode==0:
            self.tryfunc(hhlib.HH_SetHistoLen(ct.c_int(self.dev[0]), ct.c_int(self.MAXLENCODE), byref(self.histLen)), "SetHistoLen")
        
        self.tryfunc(hhlib.HH_SetStopOverflow(ct.c_int(self.dev[0]), ct.c_int(0), ct.c_int(4294967295)), "SetStopOverflow") # 4294967295 is the max 32 bit int
        # if one of the bins overflows it cuts the measure off and puts a tag in the bin data to indicate that it overflowed

        ####### Wait > 400 ms to allow INIT and SET_SYNC_DIV commands to execute ##########
        time.sleep(0.4)

        ####### Get sync and count rates #########

        self.tryfunc(hhlib.HH_GetSyncRate(ct.c_int(self.dev[0]), byref(self.syncRate)), "GetSyncRate") # provided by the laser=
        print("\nSyncrate=%1d/s" % self.syncRate.value)

        for i in range(0, self.numChannels.value): # we'll have 2 channels: 1 for each APD
            self.tryfunc(hhlib.HH_GetCountRate(ct.c_int(self.dev[0]), ct.c_int(i), byref(self.countRate)), "GetCountRate")      
            print("Countrate[%1d]=%1d/s" % (i, self.countRate.value))
        
        time.sleep(0.2)
        ######### Check for warnings (after getting count rates!) #########

        self.tryfunc(hhlib.HH_GetWarnings(ct.c_int(self.dev[0]), byref(self.warnings)), "GetWarnings")
        if self.warnings.value != 0: 
            hhlib.HH_GetWarningsText(ct.c_int(self.dev[0]), self.warningstext, self.warnings)
            print("\n\n%s" % self.warningstext.value.decode("utf-8"))
        return None

    #def pre_phecks(self):
    """Deprecated, moved to prep_measurements()"""
        

    def run_hist_measure(self, tacq=100, test_abscounts=None):
        # tacq is the acquisition time in milliseconds
        # test_abscounts is a string that is the name of the file to write the absolute counts to (for testing purposes)

        # tacq is the acquisition time in milliseconds
        self.tryfunc(hhlib.HH_ClearHistMem(ct.c_int(self.dev[0])), "ClearHistMem")

        # Check for warnings
        self.tryfunc(hhlib.HH_GetWarnings(ct.c_int(self.dev[0]), byref(self.warnings)), "GetWarnings")
        if self.warnings.value != 0:
            hhlib.HH_GetWarningsText(ct.c_int(self.dev[0]), self.warningstext, self.warnings)
            print("\n\n%s" % self.warningstext.value.decode("utf-8"))

        ####### RUN MEASURMENT #########
        self.tryfunc(hhlib.HH_StartMeas(ct.c_int(self.dev[0]), ct.c_int(tacq)), "StartMeas")

        # while time is smaller than tacq
        self.ctcstatus = ct.c_int(0)
        while self.ctcstatus.value == 0:
            self.tryfunc(hhlib.HH_CTCStatus(ct.c_int(self.dev[0]), byref(self.ctcstatus)),\
                    "CTCStatus")
        
        # stop the measurement after tacq time has passed
        self.tryfunc(hhlib.HH_StopMeas(ct.c_int(self.dev[0])), "StopMeas")

        # Check get countrate values (will significantly slow down the measurement - only use for testing)
        if test_abscounts is not None:
            with open(test_abscounts, "a") as f:
                queried_getcounts = []
                for i in range(0, self.numChannels.value):
                    self.tryfunc(hhlib.HH_GetCountRate(ct.c_int(self.dev[0]), ct.c_int(i), byref(self.countRate)), "GetCountRate")      
                    queried_getcounts.append(self.countRate.value)
                f.write(str(queried_getcounts) + '\n')

        ######### Post Process the Data #########
        # read the count data from the machine memory
        channel_intensities = np.zeros(self.numChannels.value, dtype=np.int32)
        for i in range(0, self.numChannels.value):

            self.tryfunc(hhlib.HH_GetHistogram(ct.c_int(self.dev[0]), byref(self.counts[i]), ct.c_int(i), ct.c_int(0)), "GetHistogram")
            
            integralCount = 0
            for j in range(0, self.histLen.value):
                integralCount += self.counts[i][j]
            channel_intensities[i] = integralCount
            # print("  Integralcount[%1d]=%1.0lf" % (i,integralCount))
        
        ######### Post Checks #########
        # gets all the flags and checks if there was an overflow
        self.tryfunc(hhlib.HH_GetFlags(ct.c_int(self.dev[0]), byref(self.flags)), "GetFlags")
        if self.flags.value & self.FLAG_OVERFLOW:
            print("\n  Overflow.")
        
        return np.array(channel_intensities)
    
    def integrate_intensity(self, tacq=100, test_abscounts=None):
        return self.run_hist_measure(tacq=tacq, test_abscounts=test_abscounts)
    ###DON'T USE THIS METHOD, IT DOES NOT REFLECT THE ACTUAL COUNTS OFF THE SAMPLE 
    ###ACTUALLY I DON'T QUITE KNOW HOW IT WORKS
    
    def poll_intensity(self):
        channel_intensities = np.zeros(self.numChannels.value, dtype=np.int32)
        for i in range(0, self.numChannels.value): # we'll have 2 channels: 1 for each APD
            self.tryfunc(hhlib.HH_GetCountRate(ct.c_int(self.dev[0]), ct.c_int(i), byref(self.countRate)), "GetCountRate")   
            channel_intensities[i] = self.countRate.value
        return channel_intensities
    
    ### 2024-05-15: In progress, adding T2 mode to HH context manager
    def t2_meas(self,filename, tacq=1000):
        outputfile=open(str(filename),"wb+")
        progress=0
        sys.stdout.write("\nProgress:%9u" % progress)
        sys.stdout.flush()       
        self.tryfunc(hhlib.HH_StartMeas(ct.c_int(self.dev[0]), ct.c_int(tacq)), "StartMeas")
        while True:
            self.tryfunc(hhlib.HH_GetFlags(ct.c_int(self.dev[0]), byref(self.flags)), "GetFlags")
    
            if self.flags.value & self.FLAG_FIFOFULL > 0:
                print("\nFiFo Overrun!")
                self.stoptttr()
                break
    
            self.tryfunc(hhlib.HH_ReadFiFo(ct.c_int(self.dev[0]), byref(self.buffer), self.TTREADMAX,\
                              byref(self.nRecords)),\
                    "ReadFiFo", measRunning=True)

            if self.nRecords.value > 0:
                # We could just iterate through our buffer with a for loop, however,
                # this is slow and might cause a FIFO overrun. So instead, we shrinken
                # the buffer to its appropriate length with array slicing, which gives
                # us a python list. This list then needs to be converted back into
                # a ctype array which can be written at once to the output file
                outputfile.write((ct.c_uint*self.nRecords.value)(*self.buffer[0:self.nRecords.value]))
                # print((ct.c_uint*nRecords.value)(*buffer[0:nRecords.value]))
                progress += self.nRecords.value
                sys.stdout.write("\rProgress:%9u" % progress)
                sys.stdout.flush()
            else:
                self.tryfunc(hhlib.HH_CTCStatus(ct.c_int(self.dev[0]), byref(self.ctcstatus)),\
                    "CTCStatus")
            if self.ctcstatus.value > 0: 
                print("\nDone")
                self.stoptttr()
                break
        # Within this loop you can also read the count rates if needed.                
        self.closeDevices()
        outputfile.close()
    
    def stoptttr(self):
        retcode = hhlib.HH_StopMeas(ct.c_int(self.dev[0]))
        if retcode < 0:
            print("HH_StopMeas error %1d. Aborted." % retcode)
        self.closeDevices()


    def __enter__(self):
        self.__init__(self.mode)
        self.connect_device()
        self.prep_measurements()
        # self.pre_phecks() # This function is deprecated as of v2
        return self
    
    def __exit__(self, exc_type=None, exc_value=None, traceback=None):
        self.closeDevices()
        return None