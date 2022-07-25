import time
import tkinter as tk
from tkinter import ttk

import numpy as np
from PIL import Image, ImageTk
import json
import pandas as pd
import os
import subprocess
import io


data = pd.DataFrame()
dev_info = {}
logfiles = []

with open('source/config.json', "r") as f:
    config = json.load(f)

with open(config['logfile_def_file']) as f:
    logfile_def = json.load(f)


def text_break(break_before: str = ""):
    return break_before+'****************'


def print_to_string(*args, **kwargs):
    output = io.StringIO()
    print(*args, file=output, **kwargs)
    contents = output.getvalue()
    output.close()
    return contents


def get_logfile_list():
    return sorted(os.listdir(config['logfile_folder']))


def check_logfiles():
    global dev_info, logfiles
    logfiles = get_logfile_list()

    # check if the logfiles are all from the same system etc.
    first_run = True

    for file in logfiles:
        file_array = file.split(".")[0]
        file_array = file_array.split("-")

        if first_run:
            dev_info['type'] = file_array[0]
            dev_info['SN'] = file_array[1]
            dev_info['LF_version'] = file_array[2]
            first_timestamp = file_array[-1]

            first_run = False

        if file_array[0] != dev_info['type']:
            raise ValueError('Found files of different types!')
            break
        if file_array[1] != dev_info['SN']:
            raise ValueError('Found files of different units!')
            break
        if file_array[2] != dev_info['LF_version']:
            raise ValueError('Found files with different logfile versions!')
            break

    msg = []
    msg.append(text_break())
    msg.append('Device: {}'.format('-'.join([dev_info['type'], dev_info['SN']])))
    msg.append('Logfile count: {}'.format(len(logfiles)))
    msg.append('First timestamp: {}'.format(first_timestamp))
    msg.append('Last timestamp: {}'.format(file_array[-1]))
    msg.append(text_break())
    msg = '\n'.join(msg)
    check_label_text.set(msg)

    read_btn.configure(state='!disabled')


def exchange_header(file_header, lf_version):
    # get the dict of the LF version
    header_dict = logfile_def[lf_version]

    # loop through the file header and create a new header list
    new_header = []
    for h in file_header:
        new_header.append(header_dict[h])
    return new_header


def read_logfiles():
    global data
    msg = check_label_text.get()
    # generate a list of logfile names as logfiles[]
    msg = msg + '\nReading {} logfiles.'.format(len(logfiles))
    check_label_text.set(msg)

    df_list = []

    for file in logfiles:
        filepath = config["logfile_folder"] + file
        print(filepath)
        df = pd.read_csv(filepath, sep=";")
        df_list.append(df)

    # concatenate the list of df to one single df
    data = pd.concat(df_list, axis=0, ignore_index=True)

    # exchange the header with clear name header
    data.columns = exchange_header(data.columns, dev_info['LF_version'])

    # convert timestamp to datetime
    data['timestamp_UNIXms'] = pd.to_datetime(data['timestamp_UNIXms'], unit='ms')

    # replace 'T' and 'F' with True and False and Nan with np.nan
    data.replace({'T': True, 'F': False, 'NaN': np.nan}, inplace=True)

    # activate write button
    export_btn.state(["!disabled"])

    # write completion message
    msg = msg + '\nFinished reading {} logfiles.'.format(len(logfiles))
    msg = msg + text_break('\n')
    check_label_text.set(msg)

    # write describe analysis of logfiles to check label
    describe_str = print_to_string(data['timestamp_UNIXms'].diff().astype('timedelta64[ms]').describe(percentiles=[0.05, 0.25, 0.5, 0.75, 0.95]))
    msg = msg + '\nTimestamp difference analysis (in milliseconds):\n'
    msg = msg + describe_str
    check_label_text.set(msg)
    print(describe_str)

    # enable export button
    export_btn.configure(state="!disabled")


def export_data():
    first_timestamp = data['timestamp_UNIXms'].iloc[0].strftime('%y%m%d_%H%M%S')
    last_timestamp = data['timestamp_UNIXms'].iloc[-1].strftime('%y%m%d_%H%M%S')

    filename = "-".join([dev_info['type'], dev_info['SN'], 'export', first_timestamp, 'to', last_timestamp]) + ".csv"
    data.to_csv(filename, index=False)

    export_label_text.set(filename + ' exported.')


def open_logfile_folder():
    path = os.getcwd()
    subprocess.Popen(r'explorer '+path+'\\'+config['logfile_folder'])


root = tk.Tk()
root.geometry("800x600")
# root.resizable(False, False)

root.columnconfigure(0, weight=6)
root.rowconfigure(0)
root.rowconfigure(2, weight=3)
root.rowconfigure(4, weight=2)
root.rowconfigure(6)

check_label_text = tk.StringVar(value='Check label text...')
export_label_text = tk.StringVar(value='Export label text...')

label_style = ttk.Style()
label_style.configure('label.TLabel')

btn_style = ttk.Style()
btn_style.configure('btn.TButton', padding="4p")

btn_frame_style = ttk.Style()
btn_frame_style.configure('btn_frame.TFrame', padding="4p", background = "red")

header = ttk.Label(root, text="header")
header.grid(column=0, row=0, columnspan=2, sticky="NSEW")

sep1 = ttk.Separator(root, orient='horizontal')
sep1.grid(row=1, column=0, columnspan=2, sticky="EW")

check_label = ttk.Label(root, textvariable=check_label_text, style='label.TLabel')
check_label.grid(column=0, row=2, sticky="NEW")

btn_frame = ttk.Frame(root, style='btn_frame.TFrame')
btn_frame.grid(column=1, row=2, sticky="NSEW")

open_lf_btn = ttk.Button(btn_frame, text="Open logfile folder", style='btn.TButton', command=open_logfile_folder)
open_lf_btn.pack(fill="both")

check_btn = ttk.Button(btn_frame, text="Check files", style='btn.TButton', command=check_logfiles)
check_btn.pack(fill="both")

config_btn = ttk.Button(btn_frame, text="Open config", style='btn.TButton')
config_btn.pack(fill="both")
config_btn.configure(state='disabled')

read_btn = ttk.Button(btn_frame, text="Read logfiles", style='btn.TButton', command=read_logfiles)
read_btn.pack(fill="both")
read_btn.configure(state='disabled')

sep2 = ttk.Separator(root, orient='horizontal')
sep2.grid(row=3, column=0, columnspan=2, sticky="EW")

export_option_frame = ttk.Frame(root)
export_option_frame.grid(column=0, row=4, sticky="NSEW", columnspan=2)

export_options_txt = ttk.Label(export_option_frame, text="export_options")
export_options_txt.pack(fill="both")

export_btn_frame = ttk.Frame(root, style='btn_frame.TFrame')
export_btn_frame.grid(column=1, row=5, sticky="NSEW")

export_btn = ttk.Button(export_btn_frame, text="Export logfiles", style='btn.TButton', command=export_data)
export_btn.pack(fill="both")
export_btn.configure(state="disabled")

export_label = ttk.Label(root, textvariable=export_label_text, style='label.TLabel')
export_label.grid(column=0, row=5, sticky="NSEW")

if __name__ == '__main__':
    root.mainloop()
