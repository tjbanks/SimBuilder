# -*- coding: utf-8 -*-
"""
Created on Sat Feb 24 23:26:54 2018

@author: Tyler Banks
"""

import pandas as pd
import re
import glob
from collections import defaultdict

try:
    import Tkinter as tk # this is for python2
    import ttk
    import tkMessageBox as messagebox
except:
    import tkinter as tk # this is for python3
    from tkinter import ttk
    from tkinter import messagebox

dataset_folder = 'datasets'
cells_folder = 'cells'

cellnums_file_prefix = 'cellnumbers_'
cellnums_file_postfix = '.dat'
conndata_file_prefix = 'conndata_'
conndata_file_postfix = '.dat'

cellnums_glob = dataset_folder+'/'+ cellnums_file_prefix + '*' + cellnums_file_postfix
connections_glob = dataset_folder+'/' + conndata_file_prefix +'*'+conndata_file_postfix

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
          
            
class DialogEntryBox:
    def __init__(self, parent, text="value"):

        top = self.top = tk.Toplevel(parent)
        top.geometry('200x100')
        tk.Label(top, text=text).pack()
        
        self.value = tk.StringVar(top)
        self.confirm = False
        
        self.e = tk.Entry(top,textvariable=self.value)
        self.e.pack(padx=5)

        button_frame = tk.Frame(top)
        button_frame.pack()
        
        b = tk.Button(button_frame, text="Ok", command=self.ok)
        b.grid(pady=5, padx=5, column=0, row=0)
        
        b = tk.Button(button_frame, text="Cancel", command=self.cancel)
        b.grid(pady=5, padx=5, column=1, row=0)

    def ok(self):
        self.confirm = True
        self.top.destroy()
    def cancel(self):
        self.top.destroy()
        
class PandasTable(tk.Frame):
    '''Easily display an editable pandas dataframe in TK as a Frame (Created by Tyler Banks)'''
    '''
    root = None
    table_frame_internal = None
    table_tools_frame_internal = None
    names = [] #header for the df
    values_arr = [] #values of all rows ever entered
    entities_arr = [] #all entities in the rows
    deleted_rows = [] #keep track of what has been deleted, since we don't really delete
    '''
    def __init__(self, widget):
        super(PandasTable, self).__init__(widget)
        self.root = tk.Frame(widget,padx=5,pady=5)
        self.table_frame_internal = tk.Frame(self.root,background='white')
        self.table_tools_frame_internal = tk.Frame(self.root)
        #self.table_frame_internal.grid_forget() #Probably good housekeeping
        #self.table_frame_internal.destroy() #Re-enable for previously created
        self.table_frame_internal.grid(sticky="news",row=0,column=0)
        self.table_tools_frame_internal.grid(sticky="news",row=1,column=0)
        self.options_dict = None
        self.init_tools()
        self.data_changed = False
        self.show_header = True
        return
    
    def init_tools(self):
        addRowButton = tk.Button(self.table_tools_frame_internal, text="Add Row", command=lambda: self.add_row(None))
        addRowButton.grid(column=0, row =0, padx=5,pady=5, sticky='W')
        
    def pack(self,*args):
        super(PandasTable,self).pack(*args)
        self.root.pack(*args)
        #self.table_frame_internal.pack()
        
    def grid(self,*args):
        super(PandasTable,self).grid(*args)
        self.root.grid(*args)
        
    def set_changed(self, ch):
        self.data_changed = ch
    def change_in_data(self, *args):
        self.set_changed(True)
    def has_changed(self):
        return self.data_changed
       
    def set_dataframe(self, df, options_dict = defaultdict(list), show_header=True):
        '''Totally wipe the slate and display a new dataframe'''
        self.data_changed = False
        self.show_header = show_header
        for widget in self.table_frame_internal.winfo_children():
            widget.destroy()
        self.entities_arr = []
        self.values_arr = []
        self.deleted_rows = []
        self.options_dict = options_dict
        
        self.names = list(df)
        
        if show_header:
            for k, n in enumerate(self.names):
                var = tk.Label(self.table_frame_internal, text=n)
                var.config(width=15,relief=tk.GROOVE,background='light gray')
                var.grid(column=k, row =0, padx=5, sticky='NEWS')
                
        for i, row in df.iterrows():
            self.add_row(row)            
    
        return
    
    def get_dataframe(self):
        l = []
        for i, val_row in enumerate(self.values_arr):
            r = []
            if i not in self.deleted_rows:
                for j, val in enumerate(val_row):
                    r.append(val.get())
                l.append(r)
        return pd.DataFrame(l,columns=self.names)
    
    def add_row(self,row):
        col_arr = []
        entity_arr = []
        id = len(self.entities_arr)
        insert_i = len(self.entities_arr)+1

        if row is None:
            test = ['']*len(self.names)
            r = pd.DataFrame(test).transpose()
            r.columns = self.names
            for k, rt in r.iterrows():
                row = rt
                break
        
        for j, col in enumerate(row):
            value = tk.StringVar(self.table_frame_internal)
            value.set(col)
            value.trace("w",self.change_in_data)
            entity = None
            
            if self.options_dict is not None and self.options_dict.get(j,False):
                entity = tk.OptionMenu(self.table_frame_internal, value, *self.options_dict.get(j)[0])
                entity.config(width=20)
                entity.grid(column=j,row=insert_i,sticky='NEWS')
            else:
                entity = tk.Entry(self.table_frame_internal,textvariable=value)
                entity.place(width=20)
                entity.grid(row=insert_i,column=j,sticky='NEWS')
                
            entity_arr.append(entity)
            col_arr.append(value)
            
        remove_button = tk.Button(self.table_frame_internal,text="X", command=lambda r = id: self.del_row(r))
        remove_button.grid(row=insert_i, column=len(self.names))
        entity_arr.append(remove_button)
        
        self.entities_arr.append(entity_arr)
        self.values_arr.append(col_arr)
        
        return 
    
    def del_row(self, row):
        '''A little unsafe, we assume clean data'''
        for i,r in enumerate(self.entities_arr):
            for j,c in enumerate(r):
                if(i==row):
                    c.grid_forget()
                    c.destroy()

        for i in self.deleted_rows:
            if i == row:
                return
        self.deleted_rows.append(row)
        return
    
    def new(self):
        df = pd.DataFrame(columns=self.names)
        self.set_dataframe(df, options_dict=self.options_dict, show_header=self.show_header)
        self.add_row(None)
        return
    
def menu_bar(root):
    def hello():
        print("hello!")
        
    def about():
        messagebox.showinfo("About", "Written for Satish Nair's Computational Neuroscience Lab\n\nContributors:\nTyler Banks\nBen Latimer", icon='info')

    menubar = tk.Menu(root)
    
    # create a pulldown menu, and add it to the menu bar
    filemenu = tk.Menu(menubar, tearoff=0)
    filemenu.add_command(label="Open", command=hello)
    filemenu.add_command(label="Save", command=hello)
    filemenu.add_separator()
    filemenu.add_command(label="Exit", command=root.quit)
    menubar.add_cascade(label="File", menu=filemenu)
    
    helpmenu = tk.Menu(menubar, tearoff=0)
    helpmenu.add_command(label="About", command=about)
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
               var.config(relief=tk.GROOVE)
               var.grid(column=0, row =r, padx=5, sticky='WE') 
               
               val = tk.Entry(frame)
               val.delete(0,tk.END)
               val.insert(0,line_value.group(1))
               val.grid(column=1, row=r, sticky='E')
               
               CreateToolTip(var,line_comment.group(1))
                          
               r = r+1
           line = fp.readline()
           cnt += 1

def cells_page(root):
    
    top_option_frame = tk.LabelFrame(root, text="File Management")
    table_frame = tk.LabelFrame(root, text="Cell Numbers")
    bottom_option_frame = tk.Frame(root)
    
    top_option_frame.grid(column=0,row=0,sticky='news',padx=10,pady=5)
    table_frame.grid(column=0,row=1,sticky='news',padx=10,pady=5)
    bottom_option_frame.grid(column=0,row=2)
    
    pt = PandasTable(table_frame)
    
    cellclasses_a = []
    options = glob.glob(cellnums_glob)
    
    def generate_files_available():
        cellclasses = glob.glob(cells_glob)
        cellclasses_a.clear()
        search = 'cells\\\\class_(.+?).hoc'
        for c in cellclasses:
            m = re.search(search, c)
            if m:
                cellclasses_a.append(m.group(1))
    
    def load(*args):
        #print ("loading: " + filename.get())
        cellnums_pd = pd.read_csv(filename.get() ,delimiter=' ',\
                       skiprows=1,header=None,\
                       names = ["Friendly Cell Name", "Cell File Name", "Num Cells", "Layer Index","Real:1 Artifical:0"])
        
        pt.set_dataframe(cellnums_pd, options_dict=d)
        pt.pack()
       
    def save():
        pt_df = pt.get_dataframe()
        (nr,nc) = pt_df.shape 
        tb = pt_df.to_csv(sep=' ',header=False,index=False)
        
        file = open(filename.get(),"w")
        file.write(str(nr)+'\n')
        file.write(tb)
        file.close()
        return
    
    def new():
        if pt.has_changed():
            result = messagebox.askquestion("New", "Are you sure? Data has been changed.", icon='warning')
            if result != 'yes':
                return
        d = DialogEntryBox(root,text="New File Name:")
        root.wait_window(d.top)
        
        if d.confirm==False:
            return
        
        newfilename = dataset_folder+'\\'+cellnums_file_prefix+ d.value.get() + cellnums_file_postfix
        f = open(newfilename,"w+")
        f.close
        #pt.new()
        generate_files_available()
        #https://stackoverflow.com/questions/17580218/changing-the-options-of-a-optionmenu-when-clicking-a-button
    
        m = fileMenu.children['menu']
        m.delete(0,tk.END)
        newvalues = options
        newvalues.append(newfilename)
        for val in newvalues:
            m.add_command(label=val,command=lambda v=filename,l=val:v.set(l))
        filename.set(newfilename)
        
        pt.new()

    generate_files_available()
    
    d = defaultdict(list)
    d[1].append(cellclasses_a)
        
    #Create the choice option panel
    filename = tk.StringVar(top_option_frame)
    filename.trace("w",load)
    filename.set(options[0])
    load()#initial load
    
    fileMenu = tk.OptionMenu(top_option_frame, filename, *options)
    fileMenu.grid(column=1, row =0, padx=5, sticky='W')
    
    
    saveButton = tk.Button(top_option_frame, text="Save", command=save)
    saveButton.grid(column=2, row =0, padx=5, sticky='W')
    newButton = tk.Button(top_option_frame, text="New", command=new)
    newButton.grid(column=0, row =0, padx=5, sticky='W')
    useButton = tk.Button(top_option_frame, text="Set as NumData parameter", command=save)
    useButton.grid(column=3, row =0, padx=5, sticky='W')
    
    
    
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
    
    pt = PandasTable(root)
    pt.set_dataframe(read_connections())
    pt.pack()
    

def synapses_page(root):
    
    cellnums_pd = pd.read_csv('datasets/syndata_126.dat' ,delimiter=' ',\
                           skiprows=1,header=None,\
                           names = ["Friendly Cell Name", "Cell File Name", "Num Cells", "Layer Index","Real:1 Artifical:0"])
    pt = PandasTable(root)
    pt.set_dataframe(cellnums_pd)
    pt.pack()
        
    return

def main():
    root = tk.Tk()
    #root.resizable(0,0)
    root.title("Neuron Model Configuration (University of Missouri - Nair Lab)")
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
    page7 = ttk.Frame(nb)
    
    nb.add(page1, text='Parameters')
    nb.add(page2, text='Cells')
    nb.add(page3, text='Connections')
    nb.add(page4, text='Synapses')
    nb.add(page5, text='Phasic Data')
    nb.add(page6, text='Cell Builder')
    nb.add(page7, text='Simulation Builder')
    
    #Alternatively you could do parameters_page(page1), but wouldn't get scrolling
    bind_page(page1, parameters_page)
    bind_page(page2, cells_page)
    bind_page(page3, connections_page)
    bind_page(page4, synapses_page)
    
    root.mainloop()

main()