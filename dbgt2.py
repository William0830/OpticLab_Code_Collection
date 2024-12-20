import ctypes as ct 
from ctypes import byref
from hydraharp_intensities2 import HH400_Histo_Manager
hhlib=ct.WinDLL("hhlib64.dll")

HH400=HH400_Histo_Manager(mode=2)
HH400.__enter__()



hhlib=ct.WinDLL("hhlib64.dll")


tacq=100000

# print(HH400.tryfunc(hhlib.HH_CTCStatus(ct.c_int(HH400.dev[0]), byref(HH400.ctcstatus)),\
#                         "CTCStatus"))

import tkinter as tk
import threading
import time

class CountRate:
    def __init__(self, root):
        self.root = root
        self.root.title("Count Rate Monitor")
        
        self.label = tk.Label(root, text="", font=("Helvetica", 36))
        self.label.pack(padx=20, pady=20)
        self.value = 0


        self.label1=tk.Label(root,text="",font=("Helvetica",36))
        self.label1.pack(padx=20,pady=20)
        self.ch1=0

        self.label2=tk.Label(root,text="",font=("Helvetica",36))
        self.label2.pack(padx=20,pady=20)
        self.ch2=0



        self.update_label()

    def update_label(self):
        self.label.config(text=f"Sum: {self.value}")

        self.label1.config(text=f"CH1: {self.ch1}")
        self.label2.config(text=f"CH2: {self.ch2}")
        self.root.after(500, self.update_label)  # Update the label every 500 ms
    
    def set_value_sum(self, new_value):
        self.value = new_value
        
    def set_value_ch1(self, new_value_ch1): 
        self.ch1=new_value_ch1

    def set_value_ch2(self, new_value_ch2):
        self.ch2=new_value_ch2

def background_task(app):
    while HH400.ctcstatus.value == 0:
        HH400.tryfunc(hhlib.HH_GetCountRate(ct.c_int(HH400.dev[0]),ct.c_int(0),byref(HH400.countRate)),'GetCountRate')
        app.set_value_ch1(HH400.countRate.value)
        HH400.tryfunc(hhlib.HH_GetCountRate(ct.c_int(HH400.dev[0]),ct.c_int(1),byref(HH400.countRate)),'GetCountRate')
        app.set_value_ch2(HH400.countRate.value)
        summed=app.ch1+app.ch2
        app.set_value_sum(summed)
        time.sleep(0.15)
        if HH400.ctcstatus.value != 0:
            HH400.stoptttr()


if __name__ == "__main__":
    root = tk.Tk()
    app = CountRate(root)
    
    threading.Thread(target=background_task, args=(app,), daemon=True).start()
    
    root.mainloop()

# print(HH400.ctcstatus.value)
# print(HH400.tryfunc(hhlib.HH_StartMeas(ct.c_int(HH400.dev[0]), ct.c_int(tacq)), "StartMeas"))
# print(HH400.ctcstatus.value)


# print(HH400.tryfunc(hhlib.HH_CTCStatus(ct.c_int(HH400.dev[0]), byref(HH400.ctcstatus)),\
#                         "CTCStatus"))
