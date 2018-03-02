# -*- coding: utf-8 -*-
"""
Created on Sat Feb 24 23:26:54 2018

@author: Tyler Banks
"""
import re
import glob

try:
    import Tkinter as tk # this is for python2
    import ttk
except:
    import tkinter as tk # this is for python3
    from tkinter import ttk

dataset_folder = 'datasets'
cells_folder = 'cells'

cellnums_glob = dataset_folder+'/cellnumbers_*.dat'
connections_glob = dataset_folder+'/conndata_*.dat'

cells_glob = cells_folder+'/class_*.hoc'


class CreateToolTip(object):
    """
    create a tooltip for a given widget
    https://stackoverflow.com/questions/3221956/how-do-i-display-tooltips-in-tkinter
    """
    def __init__(self, widget, text='widget info'):
        self.waittime = 500     #miliseconds
        self.wraplength = 180   #pixels
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave)
        self.id = None
        self.tw = None

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.waittime, self.showtip)

    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)

    def showtip(self, event=None):
        x = y = 0
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        # creates a toplevel window
        self.tw = tk.Toplevel(self.widget)
        # Leaves only the label and removes the app window
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(self.tw, text=self.text, justify='left',
                       background="#ffffff", relief='solid', borderwidth=1,
                       wraplength = self.wraplength)
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tw
        self.tw= None
        if tw:
            tw.destroy()
          
            
def menu_bar(root):
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
    return menubar


#pass the method that will create the content for your frame
def bind_page(page, gen_frame):
    #### Scrollable Frame Window ####
    #https://stackoverflow.com/questions/42237310/tkinter-canvas-scrollbar
    frame = tk.Frame(page, bd=2)
    frame.pack(side="left",fill="both",expand=True)
    
    yscrollbar = tk.Scrollbar(frame)
    yscrollbar.pack(side=tk.RIGHT,fill=tk.Y)
    xscrollbar = tk.Scrollbar(frame, orient=tk.HORIZONTAL)
    xscrollbar.pack(side=tk.BOTTOM,fill=tk.X)
    
    canvas = tk.Canvas(frame, bd=0,
                    xscrollcommand=xscrollbar.set,
                    yscrollcommand=yscrollbar.set)
    
    xscrollbar.config(command=canvas.xview)
    yscrollbar.config(command=canvas.yview)
    
    f=tk.Frame(canvas)
    canvas.pack(side="left",fill="both",expand=True)
    canvas.create_window(0,0,window=f,anchor='nw')
    ###############################
    gen_frame(f)
    frame.update()
    canvas.config(scrollregion=canvas.bbox("all"))
    

def parameters_page(frame):
    '''
    Reads the parameters hoc file
    Lines should be formatted like:
    default_var("Variable","value")		// Comment to be tip
    '''
    def read_parameters():
        return
    
    def write_parameters():
        return
    
    r = 2
    filepath = 'setupfiles/parameters.hoc'  
    with open(filepath) as fp:  
       line = fp.readline()
       cnt = 1
       while line:
           m = re.search('default_var\((.+?)\)', line)
           if m:
               line_variable = re.search('\"(.+?)\"', m.group(1))
               line_value = re.search(',(.+?)$', m.group(1))
               line_comment = re.search('\/\/ (.+?)$',line)
                   
               var = tk.Label(frame, text=line_variable.group(1))
               var.grid(column=0, row =r, padx=5, sticky='W') 
               
               val = tk.Entry(frame)
               val.delete(0,tk.END)
               val.insert(0,line_value.group(1))
               val.grid(column=1, row=r, sticky='E')
               
               CreateToolTip(var,line_comment.group(1))
                          
               r = r+1
           line = fp.readline()
           cnt += 1

def cells_page(root):

    data_changed = False
    cellnums_pd = ''
    
    def re_gen_table():
        return
    
    def new_row():
        return
    
    def remove_row():
        return
    
    def load(*args):
        print ("loading: " + filename.get())
        import pandas as pd
        cellnums_pd = pd.read_csv(filename.get() ,delimiter=' ',\
                           skiprows=1,header=None,\
                           names = ["Friendly Cell Name", "Cell File Name", "Num Cells", "Layer Index","Real"])
       
    def save():
        return
    
    def new():
        return
    
    options = glob.glob(cellnums_glob)
    cellclasses = glob.glob(cells_glob)
    cellclasses_a = []
    
    search = 'cells\\\\class_(.+?).hoc'
    for c in cellclasses:
        m = re.search(search, c)
        if m:
            cellclasses_a.append(m.group(1))
    
    
    #print(cellclasses)
    
    #Create the choice option panel
    option_frame = tk.Frame(root)
    option_frame.pack()
    
    filename = tk.StringVar(option_frame)
    filename.trace("w",load)
    filename.set(options[0])
    
    fileMenu = tk.OptionMenu(option_frame, filename, *options)
    fileMenu.grid(column=0, row =0, padx=5, sticky='W')
    saveButton = tk.Button(option_frame, text="Save", command=save)
    saveButton.grid(column=1, row =0, padx=5, sticky='W')
    newButton = tk.Button(option_frame, text="New", command=save)
    newButton.grid(column=2, row =0, padx=5, sticky='W')
    
    
    #File grids
    table_frame = tk.Frame(root)
    table_frame.pack()
    
    #for reference
    cellname = tk.StringVar(option_frame)
    cellname.set(cellclasses_a[0])
    cellmenu = tk.OptionMenu(option_frame, cellname, *cellclasses_a)
    cellmenu.grid(column=3,row=0,padx=5,sticky='W')
    
    #from pandastable import Table
    #pt = Table(frame,dataframe=cellnums)
    #pt.show()
    
    
def connections_page(root):
    
    def read_connections():
        import pandas as pd
        cellnums = pd.read_csv('./datasets/conndata_100.dat',delimiter=' ',\
                           skiprows=1,header=None,\
                           names = ["Presynaptic Cell", "Postsynaptic Cell", "Synapse Weight", "Convergence","Num Synapses per Connection"])
        return cellnums
    
    def write_connections():
        return
    

    options = glob.glob('datasets/conndata_*.dat')
    filename = tk.StringVar(root)
    filename.set(options[0])
    
    w = tk.OptionMenu(root, filename, *options)
    w.pack()
    
    def ok():
        print ("value: " + filename.get())
        
    button = tk.Button(root, text="ok", command=ok)
    button.pack()
    
    #print(read_connections())
    

def main():
    root = tk.Tk()
    #root.resizable(0,0)
    root.title("Neuron Model Configuration")
    root.geometry('1000x600')
    root.config(menu=menu_bar(root))
    
    nb = ttk.Notebook(root)
    nb.pack(padx=5,pady=5,side="left",fill="both",expand=True)

    page1 = ttk.Frame(nb)
    page2 = ttk.Frame(nb)
    page3 = ttk.Frame(nb)
    page4 = ttk.Frame(nb)
    page5 = ttk.Frame(nb)
    page6 = ttk.Frame(nb)
    
    nb.add(page1, text='Parameters')
    nb.add(page2, text='Cells')
    nb.add(page3, text='Connections')
    nb.add(page4, text='Synapses')
    nb.add(page5, text='Phasic Data')
    nb.add(page6, text='Cell Builder')
    
    #Alternatively you could do parameters_page(page1), but wouldn't get scrolling
    bind_page(page1, parameters_page)
    bind_page(page2, cells_page)
    bind_page(page3, connections_page)
    
    root.mainloop()

main()