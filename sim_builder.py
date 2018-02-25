# -*- coding: utf-8 -*-
"""
Created on Sat Feb 24 23:26:54 2018

@author: Tyler Banks
"""

try:
    import Tkinter as tk # this is for python2
    import ttk
except:
    import tkinter as tk # this is for python3
    from tkinter import ttk

root = tk.Tk()
root.title("Neuron Model Configuration")
root.geometry('500x500')

def hello():
    print("hello!")


menubar = tk.Menu(root)

# create a pulldown menu, and add it to the menu bar
filemenu = tk.Menu(menubar, tearoff=0)
filemenu.add_command(label="Open", command=hello)
filemenu.add_command(label="Save", command=hello)
filemenu.add_separator()
filemenu.add_command(label="Exit", command=root.quit)
menubar.add_cascade(label="File", menu=filemenu)

helpmenu = tk.Menu(menubar, tearoff=0)
helpmenu.add_command(label="About", command=hello)
menubar.add_cascade(label="Help", menu=helpmenu)

# display the menu
root.config(menu=menubar)

rows = 0
while rows < 50:
    root.rowconfigure(rows, weight=1)
    root.columnconfigure(rows, weight=1)
    rows += 1

nb = ttk.Notebook(root)
nb.grid(row=1,column=0, columnspan=50, rowspan=49, sticky='NESW')

page1 = ttk.Frame(nb)
page2 = ttk.Frame(nb)
page3 = ttk.Frame(nb)
page4 = ttk.Frame(nb)
page5 = ttk.Frame(nb)

nb.add(page1, text='Parameters')
nb.add(page2, text='Cells')
nb.add(page3, text='Connections')
nb.add(page4, text='Synapses')
nb.add(page5, text='Phasic Data')


#test = tk.Label(page1, text="text")
#test.grid(column=0, sticky='W')

#test1 = tk.Label(page1, text="text2")
#test1.grid(column=0, sticky='W')

#variable = tk.StringVar(root)
#variable.set("one")
#w = tk.OptionMenu(page1, variable,"one","two","three" )
#w.grid(column=1, row=0, sticky='E')

#e = tk.Entry(page1)
#e.grid(column=1, row=1, sticky='E')

import re
r = 2
filepath = 'setupfiles/parameters.hoc'  
with open(filepath) as fp:  
   line = fp.readline()
   cnt = 1
   while line:
       #print("Line {}: {}".format(cnt, line.strip()))
       m = re.search('default_var\((.+?)\)', line)
       if m:
           line_text = re.search('\"(.+?)\"', m.group(1))
           if line_text:
               print(line_text.group(1))
           line_option = re.search(',(.+?)$', m.group(1))
           if line_option:
               print(line_option.group(1))
               
           temp = tk.Label(page1, text=line_text.group(1))
           temp.grid(column=0, row =r, sticky='W') 
           
           e = tk.Entry(page1)
           e.delete(0,tk.END)
           e.insert(0,line_option.group(1))
           e.grid(column=1, row=r, sticky='E')
           r = r+1
       line = fp.readline()
       cnt += 1



root.mainloop()