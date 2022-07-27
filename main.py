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
import pickle


dev_info = {}
logfiles = []
config = {}
logfile_def = {}
root_path = os.getcwd()
config_json_path = os.path.join(root_path, "source", "config.json")
logfile_def_path = os.path.join(root_path, "source", "logfile_def.json")

def load_config_file():
    global config, logfile_def

    with open(config_json_path, "r") as f:
        config = json.load(f)
    for key in config:
        if type(config[key]) == str:
            config[key].replace("\\", '/')

    with open(logfile_def_path, "r") as f:
        logfile_def = json.load(f)

    str_separate_nonconsecutive.set("Separate non-consecutive timeseries (timedelta > {}s)".format(config["consecutive_threshold"]))


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
    subprocess.Popen('notepad.exe '+config_json_path).wait()

    # replace any "\" with "/" in the file
    with open(config_json_path, "r") as f:
        fdata = f.read()
    fdata = fdata.replace("\\", "/")
    with open(config_json_path, "w") as f:
        f.write(fdata)

    load_config_file()
    check_label_text.set('Config File updated and reloaded!')


def get_logfile_list():
    return sorted(os.listdir(config['logfile_folder']))


def check_logfiles():
    global dev_info, logfiles
    logfiles = get_logfile_list()

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

    desc_df = pd.DataFrame()

    for dev in dev_info:
        msg_list.append(' ')
        msg_list.append('Reading {}'.format(dev))
        check_label_text.set('\n'.join(msg_list))

        df_list = []

        for file in dev_info[dev]['files']:
            filepath = os.path.join(config['logfile_folder'], file)
            df = pd.read_csv(filepath, sep=";")
            df_list.append(df)

        # concatenate the list of df to one single df
        data = pd.concat(df_list, axis=0, ignore_index=True)

        # exchange the header with clear name header
        data.columns = exchange_header(data.columns, dev_info[dev]['lf'])

        # convert timestamp to datetime and set as index
        data['timestamp_UNIXms'] = pd.to_datetime(data['timestamp_UNIXms'], unit='ms')
        data.rename(columns={'timestamp_UNIXms': 'timestamp_UTC'}, inplace=True)
        data['timestamp_UTC'] = data['timestamp_UTC'].dt.tz_localize('UTC')
        data = data.set_index('timestamp_UTC')

        # replace 'T' and 'F' with True and False and Nan with np.nan
        data.replace({'T': True, 'F': False, 'NaN': np.nan}, inplace=True)

        # append the data into the dictionary
        dev_info[dev]['data'] = data

        # append the index to the desc_df
        desc_df[dev] = data.index.to_series().diff().dt.total_seconds()

        # check if non consecutive timeseries
        idx_diff = data.index.to_series().diff().dt.total_seconds()
        indices = data[idx_diff > config["consecutive_threshold"]].index
        # print(data.index[-1])
        last_idx = pd.Index([data.index[-1]])
        indices = indices.append([last_idx])
        dev_info[dev]['non_consecutive'] = indices
        print(dev_info[dev]['non_consecutive'])



    # activate export button
    export_btn.state(["!disabled"])

    # write completion message
    msg_list.append(text_break())
    msg_list.append('Finished reading.')
    msg_list.append(text_break())
    msg_list.append('Timedelta analysis in seconds:')
    msg_list.append(print_to_string(desc_df.describe()))
    msg_list.append(text_break())
    msg_list.append('Non-consecutive timeseries:\t' + '\t'.join([str(len(dev_info[dev]['non_consecutive'])) for dev in dev_info]))
    check_label_text.set('\n'.join(msg_list))

    # enable export button
    export_btn.configure(state="!disabled")


def export_data():

    if int_combine_pickle.get() == 1:
        export_combined_pickle()

    export_text_list = []
    for dev in dev_info:
        data_raw = dev_info[dev]['data']

        # reduce timestep if option chosen
        if int_change_timestep.get() == 1:
            new_timestep = entry_timestep.get()+'s'
            data_raw = data_raw.resample(new_timestep).mean()

        # separate non consecutive timeseries if option chosen
        if int_separate_nonconsecutive.get() == 1:
            datas = separate_non_consecutives(data_raw, dev_info[dev]['non_consecutive'])
        else:
            datas = [data_raw]

        for data in datas:
            # generate the filename
            first_timestamp = data.index[0].strftime('%y%m%d_%H%M%S')
            last_timestamp = data.index[-1].strftime('%y%m%d_%H%M%S')
            filename = "-".join([dev_info[dev]['type'], dev_info[dev]['sn'], 'export', first_timestamp, 'to', last_timestamp])+".csv"

            # check if pickle save
            if int_store_pickle.get() == 1:
                data.to_pickle(filename+".pkl")

            if int_store_excel.get() == 1:
                # check if MET timestamp conversion
                if int_convert_MET_timestamp.get() == 1:
                    data['timestamp_MET-MEST'] = data.index.tz_convert('Europe/Vienna')

                # check if UNIX int to be added
                if int_add_UNIX_int.get() == 1:
                    data['timestamp_UNIX'] = (data.index - pd.Timestamp("1970-01-01", tz='UTC')) // pd.Timedelta('1s')

                # check if EXCEL timestamp
                if int_add_EXCEL_UTC_timestamp.get() == 1:
                    data['timestamp_EXCEL_UTC'] = (((data.index - pd.Timestamp("1970-01-01", tz='UTC')) // pd.Timedelta('1s')) / 86400) + 25569

                # check if EXCEL MET timestamp
                if int_add_EXCEL_MET_timestamp.get() == 1:
                    timestamp_met = data.index[0].tz_convert('Europe/Vienna')
                    utc_offset = timestamp_met.utcoffset().seconds
                    data['timestamp_EXCEL_MET-MEST'] = (((data.index - pd.Timestamp("1970-01-01", tz='UTC')) // pd.Timedelta('1s') + utc_offset) / 86400) + 25569

                # write csv file
                data.to_csv(os.path.join(config['export_folder']+filename))

        export_text_list.append(filename + ' exported.')
    export_label_text.set('\n'.join(export_text_list))


def separate_non_consecutives(data, timestamps):
    data_list = []
    ts_start = data.index[0]
    for ts in timestamps:
        new_df = data.loc[ts_start:ts][:-1]
        data_list.append(new_df)
        ts_start = ts
    return data_list


def open_logfile_folder():
    command = 'explorer '+os.path.abspath(config['logfile_folder']+'/"')
    subprocess.Popen(command)


def test_something():
    pass


def export_combined_pickle():
    filename = 'dev_info-'+'-'.join(dev_info.keys())+'.pkl'
    with open (filename, 'wb') as f:
        pickle.dump(dev_info, f)


root = tk.Tk()
root.geometry("800x800")
# root.resizable(False, False)

root.columnconfigure(0, weight=6)
root.rowconfigure(2, weight=3)


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

logo = ImageTk.PhotoImage(Image.open(os.path.join(root_path, 'source/PBX_Logo_black_small.png')))
header = ttk.Label(root, image=logo, style='header.TLabel')
header.grid(column=0, row=0, columnspan=2, sticky="E")
#
# header = ttk.Label(root, text="header", style='header.TLabel')
# header.grid(column=0, row=0, columnspan=2, sticky="E")

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

export_option_frame.columnconfigure(0, weight=1)
export_option_frame.columnconfigure(1, weight=1)

int_add_UNIX_int = tk.IntVar(value=0)
cb_add_UNIX_int = ttk.Checkbutton(export_option_frame, text='Add UNIX (time since epoch)', variable=int_add_UNIX_int)
cb_add_UNIX_int.grid(row=0, column=0, sticky='W')

int_add_EXCEL_UTC_timestamp = tk.IntVar(value=0)
cb_add_EXCEL_timestamp = ttk.Checkbutton(export_option_frame, text='Add MS EXCEL (UTC) timestamp', variable=int_add_EXCEL_UTC_timestamp)
cb_add_EXCEL_timestamp.grid(row=1, column=0, sticky='W')

int_add_EXCEL_MET_timestamp = tk.IntVar(value=0)
cb_add_EXCEL_timestamp = ttk.Checkbutton(export_option_frame, text='Add MS EXCEL (MET/MEST) timestamp', variable=int_add_EXCEL_MET_timestamp)
cb_add_EXCEL_timestamp.grid(row=2, column=0, sticky='W')
# cb_add_EXCEL_timestamp.configure(state="disabled")

int_convert_MET_timestamp = tk.IntVar(value=0)
cb_add_MET_timestamp = ttk.Checkbutton(export_option_frame, text='Add string MET/MEST timestamp', variable=int_convert_MET_timestamp)
cb_add_MET_timestamp.grid(row=3, column=0, sticky='W')

int_separate_nonconsecutive = tk.IntVar(value=0)
str_separate_nonconsecutive = tk.StringVar(value="Separate non-consecutive timeseries (timedelta > {}s)".format(10))
cb_separate_nonconsecutive = ttk.Checkbutton(export_option_frame, textvariable=str_separate_nonconsecutive, variable=int_separate_nonconsecutive)
cb_separate_nonconsecutive.grid(row=0, column=1, sticky="W")
# cb_separate_nonconsecutive.configure(state='disabled')

timestep_frame = tk.Frame(export_option_frame)
timestep_frame.grid(row=1, column=1, sticky="W")
int_change_timestep = tk.IntVar(value=0)
cb_change_timestep = ttk.Checkbutton(timestep_frame, text="Change timestep to:  ", variable=int_change_timestep)
cb_change_timestep.pack(side="left", anchor="w")
entry_timestep = ttk.Entry(timestep_frame)
entry_timestep.pack(side="left", anchor="w")
label_timestep = ttk.Label(timestep_frame, text='seconds')
label_timestep.pack(side="left")

int_store_pickle = tk.IntVar(value=0)
cb_store_pickle = ttk.Checkbutton(export_option_frame, text="Export pickle", variable=int_store_pickle)
cb_store_pickle.grid(row=2, column=1, sticky="W")

int_combine_pickle = tk.IntVar(value=0)
cb_combine_pickle = ttk.Checkbutton(export_option_frame, text="Export combined pickle", variable=int_combine_pickle)
cb_combine_pickle.grid(row=4, column=1, sticky="W")

int_store_excel = tk.IntVar(value=1)
cb_store_excel = ttk.Checkbutton(export_option_frame, text="Export excel", variable=int_store_excel)
cb_store_excel.grid(row=3, column=1, sticky="W")

export_btn_frame = ttk.Frame(root, style='btn_frame.TFrame')
export_btn_frame.grid(column=1, row=5, sticky="NSEW")

export_btn = ttk.Button(export_btn_frame, text="Export logfiles", style='btn.TButton', command=export_data)
export_btn.pack(fill="both")
export_btn.configure(state="disabled")

# test_btn = ttk.Button(export_btn_frame, text="test button", command=test_something)
# test_btn.pack(fill="both")

export_label = ttk.Label(root, textvariable=export_label_text, style='label.TLabel')
export_label.grid(column=0, row=5, sticky="NSEW")

if __name__ == '__main__':
    load_config_file()
    root.mainloop()
