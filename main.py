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


dev_info = {}
logfiles = []
config = {}
logfile_def = {}


def load_config_file():
    global config, logfile_def
    with open('source/config.json', "r") as f:
        config = json.load(f)
    for key in config:
        config[key].replace("\\", '/')


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


def open_config():
    path = os.getcwd()
    subprocess.Popen('notepad.exe '+path+'\\source\\config.json').wait()
    load_config_file()
    check_label_text.set('Config File updated and reloaded!')


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
        dev_id = '-'.join(file_array[0:2])
        if not dev_id in dev_info.keys():
            dev_info[dev_id] = {}
            dev_info[dev_id]['type'] = file_array[0]
            dev_info[dev_id]['sn'] = file_array[1]
            dev_info[dev_id]['lf'] = file_array[2]
            dev_info[dev_id]['files'] = []

        if file_array[2] != dev_info[dev_id]['lf']:
            raise ValueError('Cannot operate on different logfile versions for the same serial number!')

        dev_info[dev_id]['files'].append(file)

    msg = []
    msg.append(text_break())
    msg.append(text_break())
    msg.append('CHECK INFO:')
    for dev in dev_info:
        msg.append('Device: {}'.format(dev))
        msg.append('File count: {}'.format(len(dev_info[dev]['files'])))
        dev_info[dev]['files'] = sorted(dev_info[dev]['files'])
        first_timestamp = dev_info[dev]['files'][0].split('.')[0].split('-')[-1]
        last_timestamp = dev_info[dev]['files'][-1].split('.')[0].split('-')[-1]
        msg.append('First file: {}'.format(first_timestamp))
        msg.append('Last file: {}'.format(last_timestamp))
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
    global dev_info
    msg = check_label_text.get()
    # generate a list of logfile names as logfiles[]
    msg_list = [msg]
    msg_list.append(text_break())
    msg_list.append('READING FILES')
    check_label_text.set('\n'.join(msg_list))

    for dev in dev_info:
        msg_list.append(' ')
        msg_list.append('Reading {}'.format(dev))
        check_label_text.set('\n'.join(msg_list))

        df_list = []

        for file in dev_info[dev]['files']:
            filepath = config["logfile_folder"] + file
            df = pd.read_csv(filepath, sep=";")
            df_list.append(df)

        # concatenate the list of df to one single df
        data = pd.concat(df_list, axis=0, ignore_index=True)

        # exchange the header with clear name header
        data.columns = exchange_header(data.columns, dev_info[dev]['lf'])

        # convert timestamp to datetime and rename the column
        data['timestamp_UNIXms'] = pd.to_datetime(data['timestamp_UNIXms'], unit='ms')
        data.rename(columns={'timestamp_UNIXms': 'timestamp_UTC'}, inplace=True)
        data['timestamp_UTC'] = data['timestamp_UTC'].dt.tz_localize('UTC')

        # replace 'T' and 'F' with True and False and Nan with np.nan
        data.replace({'T': True, 'F': False, 'NaN': np.nan}, inplace=True)

        # append the data into the dictionary
        dev_info[dev]['data'] = data

    # activate write button
    export_btn.state(["!disabled"])

    # write completion message
    msg_list.append(text_break())
    msg_list.append('Finished reading.')
    check_label_text.set('\n'.join(msg_list))

    # # write describe analysis of logfiles to check label
    # describe_str = print_to_string(data['timestamp_UTC'].diff().astype('timedelta64[ms]').describe(percentiles=[0.05, 0.25, 0.5, 0.75, 0.95]))
    # msg = msg + '\nTimestamp difference analysis (in milliseconds):\n'
    # msg = msg + describe_str
    # check_label_text.set(msg)
    # print(describe_str)

    # enable export button
    export_btn.configure(state="!disabled")


def export_data():
    export_text_list = []
    for dev in dev_info:
        data = dev_info[dev]['data']

        # generate the filename
        first_timestamp = data['timestamp_UTC'].iloc[0].strftime('%y%m%d_%H%M%S')
        last_timestamp = data['timestamp_UTC'].iloc[-1].strftime('%y%m%d_%H%M%S')
        filename = "-".join([dev_info[dev]['type'], dev_info[dev]['sn'], 'export', first_timestamp, 'to', last_timestamp]) + ".csv"

        # check if MET timestamp conversion
        if int_convert_MET_timestamp.get() == 1:
            data['timestamp_MET-MEST'] = data['timestamp_UTC'].dt.tz_convert('Europe/Vienna')

        # check if UNIX int to be added
        if int_add_UNIX_int.get() == 1:
            data['timestamp_UNIX'] = (data['timestamp_UTC'] - pd.Timestamp("1970-01-01", tz='UTC')) // pd.Timedelta('1s')

        # check if EXCEL timestamp
        if int_add_EXCEL_UTC_timestamp.get() == 1:
            data['timestamp_EXCEL'] = (((data['timestamp_UTC'] - pd.Timestamp("1970-01-01",tz='UTC')) // pd.Timedelta('1s')) / 86400) + 25569

        if int_add_EXCEL_MET_timestamp.get() == 1:
            data['timestamp_EXCEL_UTC'] = (((data['timestamp_UTC'].dt.tz_convert('Europe/Vienna') - pd.Timestamp("1970-01-01",tz='UTC')) // pd.Timedelta('1s')) / 86400) + 25569


        # write csv file
        data.to_csv(filename, index=False)

        export_text_list.append(filename + ' exported.')
    export_label_text.set('\n'.join(export_text_list))


def open_logfile_folder():
    path = os.getcwd()
    subprocess.Popen(r'explorer '+path+'\\'+config['logfile_folder'])


root = tk.Tk()
root.geometry("800x600")
# root.resizable(False, False)

root.columnconfigure(0, weight=6)
root.rowconfigure(0)
root.rowconfigure(2, weight=3)
root.rowconfigure(4)
root.rowconfigure(6)

check_label_text = tk.StringVar(value='Check label text...')
export_label_text = tk.StringVar(value='Export label text...')

label_style = ttk.Style()
label_style.configure('label.TLabel')

header_style = ttk.Style()
header_style.configure('header.TLabel', padding="8p")

btn_style = ttk.Style()
btn_style.configure('btn.TButton', padding="4p")

btn_frame_style = ttk.Style()
btn_frame_style.configure('btn_frame.TFrame', padding="4p")

logo = ImageTk.PhotoImage(Image.open('source/PBX_Logo_black_small.png'))
header = ttk.Label(root, image=logo, style='header.TLabel')
header.grid(column=0, row=0, columnspan=2, sticky="E")

sep1 = ttk.Separator(root, orient='horizontal')
sep1.grid(row=1, column=0, columnspan=2, sticky="EW")

check_label = ttk.Label(root, textvariable=check_label_text, style='label.TLabel')
check_label.grid(column=0, row=2, sticky="NEW")

btn_frame = ttk.Frame(root, style='btn_frame.TFrame')
btn_frame.grid(column=1, row=2, sticky="NSEW")

open_lf_btn = ttk.Button(btn_frame, text="Open logfile folder", style='btn.TButton', command=open_logfile_folder)
open_lf_btn.pack(fill="both")

config_btn = ttk.Button(btn_frame, text="Open config", style='btn.TButton', command=open_config)
config_btn.pack(fill="both")

check_btn = ttk.Button(btn_frame, text="Check files", style='btn.TButton', command=check_logfiles)
check_btn.pack(fill="both")

read_btn = ttk.Button(btn_frame, text="Read logfiles", style='btn.TButton', command=read_logfiles)
read_btn.pack(fill="both")
read_btn.configure(state='disabled')

sep2 = ttk.Separator(root, orient='horizontal')
sep2.grid(row=3, column=0, columnspan=2, sticky="EW")

export_option_frame = ttk.Frame(root)
export_option_frame.grid(column=0, row=4, sticky="NSEW", columnspan=2)

int_add_UNIX_int = tk.IntVar(value=0)
cb_add_UNIX_int = ttk.Checkbutton(export_option_frame, text='Add UNIX (time since epoch)', variable=int_add_UNIX_int)
cb_add_UNIX_int.grid(row=0, column=0, sticky='W')

int_add_EXCEL_UTC_timestamp = tk.IntVar(value=0)
cb_add_EXCEL_timestamp = ttk.Checkbutton(export_option_frame, text='Add MS EXCEL (UTC) timestamp', variable=int_add_EXCEL_UTC_timestamp)
cb_add_EXCEL_timestamp.grid(row=1, column=0, sticky='W')

int_add_EXCEL_MET_timestamp = tk.IntVar(value=0)
cb_add_EXCEL_timestamp = ttk.Checkbutton(export_option_frame, text='Add MS EXCEL (MET/MEST) timestamp', variable=int_add_EXCEL_MET_timestamp)
cb_add_EXCEL_timestamp.grid(row=2, column=0, sticky='W')

int_convert_MET_timestamp = tk.IntVar(value=0)
cb_add_MET_timestamp = ttk.Checkbutton(export_option_frame, text='Add string MET/MEST timestamp', variable=int_convert_MET_timestamp)
cb_add_MET_timestamp.grid(row=3, column=0, sticky='W')

export_btn_frame = ttk.Frame(root, style='btn_frame.TFrame')
export_btn_frame.grid(column=1, row=5, sticky="NSEW")

export_btn = ttk.Button(export_btn_frame, text="Export logfiles", style='btn.TButton', command=export_data)
export_btn.pack(fill="both")
export_btn.configure(state="disabled")

export_label = ttk.Label(root, textvariable=export_label_text, style='label.TLabel')
export_label.grid(column=0, row=5, sticky="NSEW")

if __name__ == '__main__':
    load_config_file()
    root.mainloop()
