import time
import tkinter as tk
from tkinter import ttk

import numpy as np
from PIL import Image, ImageTk
import json
import pandas as pd
import os


data = pd.DataFrame()
dev_info = {}

with open('source/config.json', "r") as f:
    config = json.load(f)

with open(config['logfile_def_file']) as f:
    logfile_def = json.load(f)


def get_logfile_list():
    return sorted(os.listdir(config['logfile_folder']))


def check_logfiles(logfiles):
    global dev_info
    # check if the logfiles are all from the same system etc.
    first_run = True

    for file in logfiles:
        file_array = file.split(".")[0]
        file_array = file_array.split("-")

        if first_run:
            dev_info['type'] = file_array[0]
            dev_info['SN'] = file_array[1]
            dev_info['LF_version'] = file_array[2]

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
    # generate a list of logfile names as logfiles[]
    logfiles = get_logfile_list()

    # check logfiles in folder
    check_logfiles(logfiles)

    read_txt.set('Reading {} logfiles.'.format(len(logfiles)))

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
    write_btn.state(["!disabled"])

    # write completion message
    read_txt.set('{} logfiles read.'.format(len(logfiles)))


def write_csv():
    first_timestamp = data['timestamp_UNIXms'].iloc[0].strftime('%y%m%d_%H%M%S')
    last_timestamp = data['timestamp_UNIXms'].iloc[-1].strftime('%y%m%d_%H%M%S')

    filename = "-".join([dev_info['type'], dev_info['SN'], 'export', first_timestamp, 'to', last_timestamp]) + ".csv"
    data.to_csv(filename, index=False)


tk_root = tk.Tk()
tk_root.geometry("400x400")
tk_root.title('PBX Logfile Preprocessing')

read_txt = tk.StringVar(tk_root, value='Click analyse...')

tk_header = ttk.Label(tk_root, text="pbx Logfile Preprocessing")
tk_header.pack()

read_btn = ttk.Button(tk_root, text="Read logfiles", command=read_logfiles)
read_btn.pack()

read_label = ttk.Label(tk_root, textvariable=read_txt)
read_label.pack()

write_btn = ttk.Button(tk_root, text='Write CSV', command=write_csv)
write_btn.pack()
write_btn.state(["disabled"])

write_label_text = tk.StringVar()
write_label = ttk.Label(tk_root, textvariable=write_label_text)
write_label.pack()

if __name__ == '__main__':
    tk_root.mainloop()
