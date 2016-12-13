# -*- coding: utf-8 -*-
'''MX100Parse.py: Functions for parsing/exporting/plotting specified columns from MX100 log files

__author__ = "Jason M. Battle"
'''

import os
import re
import time
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

class MX1100():
    
    def __init__(self):
        self.frame = pd.DataFrame()

    def __self__(self):
        return self.frame

    def find_logs(self, dirpath):
        self.logfiles = glob.glob(dirpath + '\*mxs*.txt')

    def to_dataframe(self, logfile, col_names):       
        with open(logfile, 'rb') as f: 
        
            # Find starting test start date and time
            start_date = filter(None, [re.findall(r'.*Start Time.*\"(\d+/\d+/\d+)\".*', line) for line in f.readlines()])[0][0]
            f.seek(0)
            start_time = filter(None, [re.findall(r'.*Start Time.*\"(\d+:\d+:\d+)\".*', line) for line in f.readlines()])[0][0]
            f.seek(0)
            
            # Find header row then time column index
            hdr_row = np.where([re.findall(r'.*,\"Time\",.*', line) for line in f.readlines()])[0][0]
            f.seek(0)
            time_col = np.where([re.findall(r'\"Time\"', val) for val in f.readlines()[hdr_row].split(',')])[0][0]
            f.seek(0)
            
            # Grab time column and offset all values according to delta between start time and first column value
            times = [line.split(',')[time_col].replace('"', '').replace('\r\n', '') for line in f.readlines()[hdr_row+1:]]
            times = np.array([time.mktime(time.strptime(r'%s %s' % (start_date, val), '%Y/%m/%d %H:%M:%S')) for val in times])
            time_offset = time.mktime(time.strptime(r'%s %s' % (start_date, start_time), '%Y/%m/%d %H:%M:%S'))
            times = times - (times[0] - time_offset)
            time_stamps = np.array([time.strftime('%H:%M:%S', time.localtime(val)) for val in times])
            
            # Find elapsed time by offsetting by the first column value for post-corrected array
            time_elapsed = times - times[0]
            f.seek(0)
            
            # Store all data column headers
            hdrs = [val.replace('"', '').replace('\r\n', '') for val in f.readlines()[hdr_row-2].split(',')[4:]]
            f.seek(0)
            
            # Populate a dictionary indexed by hdrs as keys
            data = {}
            data['Time_stamps'] = time_stamps
            data['Time_elapsed'] = time_elapsed
            
            for index, label in enumerate(hdrs):
                data['%s' % label] = np.array([line.split(',')[index+4].replace('"','').replace('\r\n', '') for line in f.readlines()[hdr_row+1:]])
                if '.' in data['%s' % label][0]:
                    data['%s' % label] = (data['%s' % label].astype(float) * 10**3).astype(int)
                else:
                    data['%s' % label] = data['%s' % label].astype(int)
                f.seek(0)

            self.frame['Time_stamps'] = data['Time_stamps']
            self.frame['Time_elapsed'] = data['Time_elapsed']

            for name in col_names:
                self.frame['%s' % name] = data['%s' % name]

    def to_excel(self, logfile):       
        workbook = pd.ExcelWriter(os.path.splitext(logfile)[0] + '.xlsx')
        self.frame.to_excel(workbook, 'Data', index=False)
        workbook.save()
 
    def to_plot(self, logfile, title, show_hrs=True):
        from itertools import cycle
        fig = plt.figure(figsize=(24, 12))

        axes = {}
        cmap = cycle(['green','red','blue'])        

        for index, col in enumerate(self.frame.columns[2:]):

            axes['ax%i' % (index+1)] = fig.add_subplot('21%i' % (index+1))

            if show_hrs == True:
                axes['ax%i' % (index+1)].plot(self.frame['Time_elapsed'] / 3600., self.frame.iloc[:, index+2], c=cmap.next())
                axes['ax%i' % (index+1)].set_xlabel('$Time [hrs]$')
            else:
                axes['ax%i' % (index+1)].plot(self.frame['Time_elapsed'], self.frame.iloc[:, index+2], c=cmap.next())
                axes['ax%i' % (index+1)].set_xlabel('$Time [secs]$')
            if ('I' in col) or ('i' in col):
                axes['ax%i' % (index+1)].set_ylabel('$Current [mA]$')
            elif ('V' in col) or ('v' in col):
                axes['ax%i' % (index+1)].set_ylabel('$Voltage [mV]$')                
            else:
                pass
            axes['ax%i' % (index+1)].grid()
            
        axes['ax1'].set_title(title)                  
        fig.savefig(os.path.splitext(logfile)[0] + '.jpeg')
