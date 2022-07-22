import tkinter as tk
from tkinter import ttk

root = tk.Tk()
root.geometry("400x600")
root.resizable(False, False)

root.columnconfigure(0, weight=6)
root.columnconfigure(1)
root.rowconfigure(0)
root.rowconfigure(1, weight=3)
root.rowconfigure(2, weight=2)
root.rowconfigure(3, weight=1)

label_style = ttk.Style()
label_style.configure('label.TLabel', background="red")

btn_style = ttk.Style()
btn_style.configure('btn.TButton', padding="2p")

header = ttk.Label(root, text="header", background="green", borderwidth="10p")
header.grid(column=0, row=0, columnspan=2, sticky="NSEW")

check_label = ttk.Label(root, text="check label", style='label.TLabel')
check_label.grid(column=0, row=1, sticky="NSEW")

btn_frame = ttk.Frame(root, padding="2p")
btn_frame.grid(column=1, row=1, sticky="N")

open_lf_btn = ttk.Button(btn_frame, text="open_lf_btn", style='btn.TButton')
open_lf_btn.pack()

check_btn = ttk.Button(btn_frame, text="check_btn", style='btn.TButton')
check_btn.pack()

config_btn = ttk.Button(btn_frame, text="config_btn", style='btn.TButton')
config_btn.pack()

read_btn = ttk.Button(btn_frame, text="read_btn", style='btn.TButton')
read_btn.pack()

export_options = ttk.Label(root, text="export_options", background="green")
export_options.grid(column=0, row=2, sticky="NSEW")

export_btn = ttk.Button(root, text="export_btn", style='btn.TButton')
export_btn.grid(column=1, row=2, sticky="N")

export_label = ttk.Label(root, text="export_label", style='label.TLabel')
export_label.grid(column=0, row=3, sticky="NSEW")


if __name__ == '__main__':
    root.mainloop()
