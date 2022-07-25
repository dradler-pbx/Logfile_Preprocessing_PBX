import tkinter as tk
from tkinter import ttk

root = tk.Tk()


def open_top_level():
    top_level = tk.Toplevel(root)
    btn_close = ttk.Button(top_level, text="Close", command=top_level.destroy)
    btn_close.pack()


btn = ttk.Button(root, text='Open Top Level', command=open_top_level)
btn.pack()

if __name__=="__main__":
    root.mainloop()