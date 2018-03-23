# -*- coding: utf-8 -*-
"""
Created on Sat Feb 24 23:26:54 2018

@author: Tyler Banks
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import os
import subprocess
import re
import glob
from collections import defaultdict
import threading

try:
    import Tkinter as tk # this is for python2
    import ttk
    import tkMessageBox as messagebox
except:
    import tkinter as tk # this is for python3
    from tkinter import ttk
    from tkinter import messagebox

root = tk.Tk()

dataset_folder = 'datasets'
cells_folder = 'cells'
results_folder = 'results'

cellnums_file_prefix = 'cellnumbers_'
cellnums_file_postfix = '.dat'
conndata_file_prefix = 'conndata_'
conndata_file_postfix = '.dat'
syndata_file_prefix = 'syndata_'
syndata_file_postfix = '.dat'
phasicdata_file_prefix = 'phasic_'
phasicdata_file_postfix = '.dat'
trace_file_prefix = 'trace_'
trace_file_postfix = '.dat'

cellnums_glob = os.path.join(dataset_folder,cellnums_file_prefix + '*' + cellnums_file_postfix)
connections_glob = os.path.join(dataset_folder, conndata_file_prefix +'*'+ conndata_file_postfix)
syndata_glob = os.path.join(dataset_folder, syndata_file_prefix + '*' + syndata_file_postfix)
phasicdata_glob = os.path.join(dataset_folder, phasicdata_file_prefix + '*' + phasicdata_file_postfix)
results_glob = os.path.join(results_folder,'*','')

cells_glob = cells_folder+'/class_*.hoc'

cellclasses = [fn for fn in glob.glob(cells_glob) 
         if not os.path.basename(fn).startswith('class_cell_template')]


class Autoresized_Notebook(ttk.Notebook):
    def __init__(self, master=None, **kw):
        ttk.Notebook.__init__(self, master, **kw)
        self.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def _on_tab_changed(self,event):
        event.widget.update_idletasks()
        tab = event.widget.nametowidget(event.widget.select())
        event.widget.configure(height=tab.winfo_reqheight())

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
    def __init__(self, parent, text="value", lefttext="",righttext=""):

        top = self.top = tk.Toplevel(parent)
        top.geometry('350x100')
        tk.Label(top, text=text).grid(row=0,column=1,sticky="WE")
        
        self.value = tk.StringVar(top)
        self.confirm = False
        
        tk.Label(top, text=lefttext,width=20, anchor="e").grid(row=1,column=0)
        
        vcmd = (top.register(self.validate),
                '%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')
        
        self.e = tk.Entry(top,textvariable=self.value, validate = 'key', validatecommand = vcmd)
        self.e.grid(row=1,column=1,columnspan=2)
        tk.Label(top, text=righttext).grid(row=1,column=3)
        
        button_frame = tk.Frame(top)
        button_frame.grid(row=2,column=1)
        
        b = tk.Button(button_frame, text="Ok", command=self.ok)
        b.grid(pady=5, padx=5, column=0, row=2, sticky="WE")
        
        b = tk.Button(button_frame, text="Cancel", command=self.cancel)
        b.grid(pady=5, padx=5, column=1, row=2, sticky="WE")
        
        tk.Label(top, text="Numbers only currently",width=20, anchor="w",fg='blue').grid(row=3,column=1,columnspan=2)
        
    def validate(self, action, index, value_if_allowed,
                       prior_value, text, validation_type, trigger_type, widget_name):

        if text in '0123456789-':
            try:
                if value_if_allowed is '':
                    return True
                float(value_if_allowed)
                return True
            except ValueError:
                return False
        else:
            return False

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
    def __init__(self, widget, show_add_row_button=True, allow_sorting=True):
        super(PandasTable, self).__init__(widget)
        self.root = tk.Frame(widget,padx=5,pady=5)
        self.table_frame_internal = tk.Frame(self.root,background='white')
        self.table_tools_frame_internal = tk.Frame(self.root)
        #self.table_frame_internal.grid_forget() #Probably good housekeeping
        #self.table_frame_internal.destroy() #Re-enable for previously created
        self.table_frame_internal.grid(sticky="news",row=0,column=0)
        self.table_tools_frame_internal.grid(sticky="news",row=1,column=0)
        self.options_dict = None
        self.data_changed = False
        self.show_header = True
        self.show_numbering = True
        self.show_delete_row = True
        self.first_column_is_header = False
        self.first_column_is_id = False
        self.show_add_row_button = show_add_row_button
        self.immutable_columns = []
        self.immutable_values = []
        self.hidden_columns = []
        self.col_width=15
        self.last_sort_by = True
        self.last_sort_by_col = ''
        self.allow_sorting = allow_sorting
        self.init_tools()
        return
    
    def init_tools(self):
        if self.show_add_row_button:
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
    
    
    def sort_by(self, col):
        if not self.allow_sorting:
            return
        
        if self.last_sort_by_col is col:
            self.last_sort_by = not self.last_sort_by #sort decending
        else:
            self.last_sort_by = True
        
        self.last_sort_by_col = col
            
        sorted_df = self.df.sort_values(by=[col], ascending=self.last_sort_by)
        self.set_dataframe(sorted_df, self.options_dict, 
                      self.show_header, self.show_numbering, 
                      self.show_delete_row, self.first_column_is_header, 
                      self.first_column_is_id, self.immutable_columns, 
                      self.immutable_values, self.hidden_columns)
       
    def set_dataframe(self, df, options_dict = defaultdict(list), \
                      show_header=True, show_numbering=True, \
                      show_delete_row=True, first_column_is_header=False, \
                      first_column_is_id= False, immutable_columns=[],\
                      immutable_values=[], hidden_columns=[]):
        '''Totally wipe the slate and display a new dataframe'''
        self.df = df
        self.data_changed = False
        self.show_header = show_header
        self.show_numbering = show_numbering
        self.show_delete_row = show_delete_row
        self.first_column_is_header = first_column_is_header
        self.first_column_is_id = first_column_is_id
        self.immutable_columns = immutable_columns
        self.hidden_columns = []#hidden_columns #Still has some minor bugs to work out, implement if needed
        
        for widget in self.table_frame_internal.winfo_children():
            widget.destroy()
        self.entities_arr = []
        self.values_arr = []
        self.deleted_rows = []
        self.options_dict = options_dict
        self.immutable_values = immutable_values
        
        
        self.names = list(df)
        
        if show_header:
            for k, n in enumerate(self.names):
                if self.first_column_is_id and k==0:
                    continue
                if k in self.hidden_columns:
                    continue
                var = tk.Label(self.table_frame_internal, text=n)
                var.config(width=self.col_width,relief=tk.GROOVE,background='light gray')
                var.bind("<Button-1>", lambda event, col=n:self.sort_by(col))
                var.grid(column=k+3, row =0, padx=1, sticky='NEWS')
                
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
        
        num = len(self.entities_arr)-len(self.deleted_rows)
        
        if self.show_numbering:
            num_button = tk.Label(self.table_frame_internal,text=str(num))
            num_button.config(relief=tk.GROOVE,background='light gray',width=3)
            num_button.grid(row=insert_i, column=0,sticky='news')
            entity_arr.append(num_button)
            
        if self.first_column_is_header:
            text = ' '
            if id < len(self.names):
                text = self.names[id]
            identity_button = tk.Label(self.table_frame_internal,text=str(text))
            identity_button.config(width=self.col_width,relief=tk.GROOVE,background='light gray')
            identity_button.grid(row=insert_i, column=1,sticky='news')
            entity_arr.append(identity_button)
               
        
        for j, col in enumerate(row):
            value = tk.StringVar(self.table_frame_internal)
            value.set(col)
            value.trace("w",self.change_in_data)
            entity = None
            #print(value.get())
            
            if j in self.hidden_columns:
                entity = tk.Entry(self.table_frame_internal,textvariable=value)
                entity.place(width=20)
                #don't display
            elif self.first_column_is_id and j==0:
                entity = tk.Label(self.table_frame_internal,text=value.get())
                entity.config(width=20,height=2,relief=tk.GROOVE,background='light gray')
                entity.grid(row=insert_i, column=2,sticky='news')
                #entity = tk.Button(self.table_frame_internal,text=value.get())
                #entity.grid(row=insert_i, column=0,sticky='news')
            elif value.get() in self.immutable_values: 
                entity = tk.Label(self.table_frame_internal,text=" ")
                entity.config(width=20,relief=tk.GROOVE,background='light gray')
                entity.grid(row=insert_i, column=j+3,sticky='news')
            elif self.options_dict is not None and self.options_dict.get(j,False):
                temp = self.options_dict.get(j)[0]
                entity = tk.OptionMenu(self.table_frame_internal, value ,*temp, '')
                entity.config(width=20)
                entity.grid(column=j+3,row=insert_i,sticky='NEWS')
            else:
                entity = tk.Entry(self.table_frame_internal,textvariable=value)
                entity.place(width=20)
                entity.grid(row=insert_i,column=j+3,sticky='NEWS')
                
            entity_arr.append(entity)
            col_arr.append(value)
           
        if self.show_delete_row:
            remove_button = tk.Button(self.table_frame_internal,text="X", command=lambda r = id: self.del_row(r))
            remove_button.grid(row=insert_i, column=len(self.names)+3,sticky='news')
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
        messagebox.showinfo("About", "Simulation Builder written for:\nProfessor Satish Nair's Neural Engineering Laboratory\nat The University of Missouri\n\nWritten by: Tyler Banks\n\nContributors: Ben Latimer\n\nInitial Neuron Code:  Bezaire et al (2016), ModelDB (accession number 187604), and McDougal et al (2017)\n\nEmail tbg28@mail.missouri.edu with questions", icon='info')

    menubar = tk.Menu(root)
    
    # create a pulldown menu, and add it to the menu bar
    filemenu = tk.Menu(menubar, tearoff=0)
    #filemenu.add_command(label="Open", command=hello)
    #filemenu.add_command(label="Save", command=hello)
    #filemenu.add_separator()
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
                    yscrollcommand=yscrollbar.set,)
    
    xscrollbar.config(command=canvas.xview)
    yscrollbar.config(command=canvas.yview)
    
    f=tk.Frame(canvas)
    canvas.pack(side="left",fill="both",expand=True)
    canvas.create_window(0,0,window=f,anchor='nw')
    ###############################
    gen_frame(f)
    frame.update()
    canvas.config(scrollregion=canvas.bbox("all"))
    

params_dict = {'aaa':tk.StringVar(root,'bbb'),\
               'loaded_cellnums':tk.StringVar(root,'none'),\
               'loaded_conndata':tk.StringVar(root,'none'),\
               'loaded_syndata':tk.StringVar(root,'none'),\
               'loaded_phasicdata':tk.StringVar(root,'none')}

def get_public_param(param):
    try:
        return params_dict[param].get()
    except KeyError:
        return None

def set_public_param(param, strvar):
    try:
        params_dict[param].set(strvar)
    except KeyError:
        params_dict[param] = strvar
    return

def reset_public_params():
    params_dict.clear()
    return


def parameters_page(root):
    '''
    Reads the parameters hoc file
    Lines should be formatted like:
    default_var("Variable","value")		// Comment to be tip
    '''
    param_has_changed = False
    params_file = os.path.join('setupfiles','parameters.hoc')
    
    top_option_frame = tk.LabelFrame(root, text="Management")
    table_frame = tk.Frame(root)
    import_export_frame = tk.LabelFrame(root, text="Import/Export")
    
    top_option_frame.grid(column=0,row=0,sticky='news',padx=10,pady=5)
    table_frame.grid(column=0,row=1,sticky='news',padx=10,pady=5)
    import_export_frame.grid(column=1,row=0,sticky='news',padx=10,pady=5)
    
    def param_changed(*args,val=True):
        param_has_changed = val
    
    class Row(tk.Frame):
        def __init__(self, parent, *args, **kwargs):
            tk.Frame.__init__(self, parent, *args, **kwargs)
            self.parent = parent
            self.root = tk.Frame(self.parent)
            self.is_string = False
            return
        
        def config(self, variable, value, comment, is_string):
            self.v_value = tk.StringVar(self.root)
            self.v_value.set(value)
            self.v_value.trace("w",param_changed)
            
            self.variable = variable
            self.comment = comment
            self.is_string = is_string
            
            frame = tk.Frame(self.root)
            var = tk.Label(frame, text=variable ,width=20,background='light gray')
            var.config(relief=tk.GROOVE)
            var.grid(column=0, row=0, padx=5, sticky='WE') 
            
            val = tk.Entry(frame,textvariable=self.v_value)
            val.grid(column=1, row=0, sticky='E')
               
            CreateToolTip(var,comment)
            frame.pack()
            return self
        
        def row_to_param_str(self):
            #default_var("RunName","testrun")		// Name of simulation run
            proto = "default_var(\"{}\",{})\t\t// {}"
            if self.is_string:
                proto = "default_var(\"{}\",\"{}\")\t\t// {}"
            line = proto.format(self.variable,self.v_value.get(),self.comment)
            return line
        
        def pack(self,*args,**kwargs):
            super(Row,self).pack(*args,**kwargs)
            self.root.pack(*args,**kwargs)
        
        def grid(self,*args,**kwargs):
            super(Row,self).grid(*args,**kwargs)
            self.root.grid(*args,**kwargs)
            
    
    row_header = ['variable','value','comment','value_is_string']
    rows=[]
    def load(filename):
        
        params = []
        with open(filename) as fp:  
           line = fp.readline()
           cnt = 1
           while line:
               m = re.search('default_var\((.+?)\)', line)
               if m:
                   line_variable = re.search('\"(.+?)\"', m.group(1)).group(1)
                   line_value = re.search(',(.+?)$', m.group(1)).group(1)
                   line_comment = re.search('\/\/ (.+?)$',line).group(1)
                   line_value_string = False
                   
                   n = re.search('\"(.*?)\"',line_value)
                   if n:
                       line_value_string = True
                       line_value=n.group(1)
                       
                   params.append([line_variable,line_value,line_comment,line_value_string])
               line = fp.readline()
               cnt += 1
               
        df = pd.DataFrame(params,columns=row_header)
        return df
    
    def save():
        file = open(params_file,"w")
        for r in rows:
            file.write(r.row_to_param_str()+"\n")
        file.close()
        
        display_app_status('Parameters \"'+params_file+'\" saved')
        
        return
    
    general_frame = tk.LabelFrame(table_frame, text="General",fg="blue")
    general_frame.grid(column=0,row=0,sticky='news',padx=10,pady=5)
    dropdown_frame = tk.LabelFrame(table_frame, text="Data Sources",fg="blue")
    dropdown_frame.grid(column=1,row=0,sticky='news',padx=10,pady=5)
    space_frame = tk.LabelFrame(table_frame, text="Spacial Config",fg="blue")
    space_frame.grid(column=0,row=1,sticky='news',padx=10,pady=5)
    print_frame = tk.LabelFrame(table_frame, text="Print/Output",fg="blue")
    print_frame.grid(column=1,row=2,sticky='news',padx=10,pady=5)
    misc_frame = tk.LabelFrame(table_frame, text="Miscellaneous",fg="blue")
    misc_frame.grid(column=0,row=2,sticky='news',padx=10,pady=5)
    lfp_frame = tk.LabelFrame(table_frame, text="LFP Config",fg="blue")
    lfp_frame.grid(column=1,row=1,sticky='news',padx=10,pady=5)
    
    
    general_vars = ['RunName', 'Scale','SimDuration','StepBy','TemporalResolution','RandomVrest','RandomVinit']
    space_vars = ['TransverseLength','LongitudinalLength','LayerHeights','SpatialResolution']
    dropdown_vars = ['ConnData','SynData','NumData','PhasicData','Connectivity','Stimulation']
    print_vars = ['PrintVoltage','PrintTerminal','PrintConnDetails','PrintCellPositions','PrintConnSummary','CatFlag','EstWriteTime','NumTraces']
    lfp_vars = ['lfp_dt','ElectrodePoint','ComputeNpoleLFP','ComputeDipoleLFP','LFPCellTypes','MaxEDist']
    
    def refresh(df):
        param_changed(val=False)
        rows.clear()
        
        padtopbot = 3
        Row(general_frame).pack(pady=padtopbot-1)
        Row(dropdown_frame).pack(pady=padtopbot-1)
        Row(space_frame).pack(pady=padtopbot-1)
        Row(print_frame).pack(pady=padtopbot-1)
        Row(misc_frame).pack(pady=padtopbot-1)
        Row(lfp_frame).pack(pady=padtopbot-1)
        
        for i, row in df.iterrows():
            temp = []
            temp.append(row.tolist())
            temp = temp[0]
            #config(self, variable, value, comment, is_string):
            
            frame = misc_frame
            if temp[0] in general_vars:
                frame=general_frame
            elif temp[0] in dropdown_vars:
                frame=dropdown_frame
            elif temp[0] in space_vars:
                frame=space_frame
            elif temp[0] in print_vars:
                frame=print_frame
            elif temp[0] in lfp_vars:
                frame=lfp_frame
            
            #This is all pages to change
            row = Row(frame).config(temp[0],temp[1],temp[2],temp[3])
            row.pack(padx=10)
            rows.append(row)
            set_public_param(temp[0],row.v_value)
    
        Row(general_frame).pack(pady=padtopbot)
        Row(dropdown_frame).pack(pady=padtopbot)
        Row(space_frame).pack(pady=padtopbot)
        Row(print_frame).pack(pady=padtopbot)
        Row(misc_frame).pack(pady=padtopbot)
        Row(lfp_frame).pack(pady=padtopbot)
        return
    
    def verify():
        display_app_status('Not implemented')
        return
        
    def import_model():
        display_app_status('Not implemented')
        return
    
    def export_model():
        display_app_status('Not implemented')
        return
    
    verifyBuildButton = tk.Button(top_option_frame, text="Verify Model Configuration", command=verify)
    verifyBuildButton.grid(column=1, row =0, padx=5, pady=5, sticky='W')
    verifyBuildButton.config(state=tk.DISABLED)
    
    saveButton = tk.Button(top_option_frame, text="Save Parameters File", command=save)
    saveButton.grid(column=0, row =0, padx=5, pady=5, sticky='W')

    
    importButton = tk.Button(import_export_frame, text="Import Model", command=import_model)
    importButton.grid(column=0, row =0, padx=5, pady=5, sticky='WE')
    importButton.config(state=tk.DISABLED)
    
    exportButton = tk.Button(import_export_frame, text="Export Model", command=export_model)
    exportButton.grid(column=0, row =1, padx=5, pady=5, sticky='WE')
    exportButton.config(state=tk.DISABLED)
    
    df = load(params_file)
    refresh(df)
    

def cells_page(root):
    
    column_names = ["Friendly Cell Name", "Cell File Name", "Number of Cells", "Layer Index","Artificial:1 Real:0"]
    
    top_option_frame = tk.LabelFrame(root, text="File Management")
    table_frame = tk.LabelFrame(root, text="Cell Numbers")
    bottom_option_frame = tk.Frame(root)
    
    top_option_frame.grid(column=0,row=0,sticky='news',padx=10,pady=5)
    table_frame.grid(column=0,row=1,sticky='news',padx=10,pady=5)
    bottom_option_frame.grid(column=0,row=2)
    
    pt = PandasTable(table_frame, show_add_row_button=True)
    
    cellclasses_a = []
    options = glob.glob(cellnums_glob)
    
    
    def generate_files_available():
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
                       names = column_names)
        cellnums_pd[column_names[2]] = cellnums_pd[column_names[2]].astype(int)
        cellnums_pd[column_names[3]] = cellnums_pd[column_names[3]].astype(int)
        cellnums_pd[column_names[4]] = cellnums_pd[column_names[4]].astype(int)
        pt.set_dataframe(cellnums_pd, options_dict=d, show_numbering=True, show_delete_row=True, first_column_is_header=False)
        pt.pack()
        set_public_param("loaded_cellnums",filename.get())
        
        display_app_status('Cells file \"'+filename.get()+'\" loaded')
       
    def save(save_to=None):
        pt_df = pt.get_dataframe()
        (nr,nc) = pt_df.shape 
        tb = pt_df.to_csv(sep=' ',header=False,index=False)
        
        if not save_to:
            save_to = filename.get()
        
        file = open(save_to,"w")
        file.write(str(nr)+'\n')
        file.write(tb)
        file.close()
        display_app_status('Cells file \"'+filename.get()+'\" saved')
    
    def new():
        if pt.has_changed():
            result = messagebox.askquestion("New", "Are you sure? Data has been changed.", icon='warning')
            if result != 'yes':
                return
        d = DialogEntryBox(root,text="New File Name:",lefttext=os.path.join(dataset_folder, cellnums_file_prefix),righttext=cellnums_file_postfix)
        root.wait_window(d.top)
        
        if d.confirm==False:
            return
        
        newfilename = os.path.join(dataset_folder, cellnums_file_prefix+ d.value.get() + cellnums_file_postfix)
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
        display_app_status('Cells file \"'+newfilename+'\" created')
        
    def new_clone():
        
        if pt.has_changed():  
            result = messagebox.askquestion("New", "Are you sure? Data has been changed.", icon='warning')
            if result != 'yes':
                return
        d = DialogEntryBox(root,text="New File Name:",lefttext=os.path.join(dataset_folder, cellnums_file_prefix),righttext=cellnums_file_postfix)
        root.wait_window(d.top)
        
        if d.confirm==False:
            return
        
        
        newfilename = os.path.join(dataset_folder,cellnums_file_prefix+ d.value.get() + cellnums_file_postfix)
        f = open(newfilename,"w+")
        f.close()
        save(save_to=newfilename)
        
        m = fileMenu.children['menu']
        m.delete(0,tk.END)
        newvalues = options
        newvalues.append(newfilename)
        for val in newvalues:
            m.add_command(label=val,command=lambda v=filename,l=val:v.set(l))
        filename.set(newfilename)
        
    
        display_app_status('Cells file \"'+filename.get()+'\" created')
        return
    
    def set_numdata_param():
        fn = filename.get()
        search = cellnums_file_prefix+'(.+?)'+cellnums_file_postfix
        m = re.search(search,fn)
        if m:
            fn = m.group(1)

        set_public_param("NumData", fn)
        display_app_status('NumData parameter set to \"'+ filename.get() +'\" in current parameters file')
        return

    def delete_current_file():
        return
    
    generate_files_available()
    
    d = defaultdict(list)
    d[1].append(cellclasses_a)
        
    #Create the choice option panel
    filename = tk.StringVar(top_option_frame)
    filename.trace("w",load)
    
    numdat = get_public_param("NumData")
    numdat = os.path.join(dataset_folder, cellnums_file_prefix + numdat + cellnums_file_postfix)
    filename.set(numdat)
    #filename.set(options[0])
        
    load()#initial load
    
    
    newButton = tk.Button(top_option_frame, text="New", command=new,width=30)
    newButton.grid(column=0, row =0, padx=5, sticky='WE')
    useButton = tk.Button(top_option_frame, text="Set as NumData parameter", command=set_numdata_param,width=30)
    useButton.grid(column=0, row =1, padx=5, sticky='W')
    
    fileMenu = tk.OptionMenu(top_option_frame, filename, *options)
    fileMenu.grid(column=1, row =0, padx=5, sticky='WE',columnspan=2)    
    
    saveButton = tk.Button(top_option_frame, text="Save", command=save)
    saveButton.grid(column=1, row =1, padx=5, pady=5, sticky='WE')
    newCloneButton = tk.Button(top_option_frame, text="Save As", command=new_clone)
    newCloneButton.grid(column=2, row =1, padx=5, sticky='WE')
    
    deleteButton = tk.Button(top_option_frame, text="Delete", command=delete_current_file)
    deleteButton.grid(column=3, row =0, padx=5, pady=5, sticky='W')
    deleteButton.config(state=tk.DISABLED)
    
    
    
def connections_page(root):
    
    class connections_adapter(object):
        
        def __init__(self, root, col, text=''):
            self.root = root
            self.col = col
            tk.Label(root, text=text ,fg='blue').pack(anchor='w')
            self.pt = PandasTable(self.root, show_add_row_button=False, allow_sorting=False)
            self.pt.pack()
            
        def read_internal(self, df, astype=None):
            df1 = df[df.columns[[0,1,self.col]]]
            pre = df1[df1.columns[0]].unique()
            pre = pd.DataFrame(pre)
            post = df1[df1.columns[1]].unique()
            vals = df1[df1.columns[2]]
            vals = pd.DataFrame(vals.values.reshape(len(pre),len(post)),columns=post)
            if astype:
                vals = vals.astype(astype)
            df1 = pd.concat([pre,vals],axis=1)
            #df1[df1.columns[self.col]] = df1[df1.columns[self.col]]
            return pd.DataFrame(df1)
        
        def get_df(self):
            pt_df = self.pt.get_dataframe()
            (nr,nc) = pt_df.shape 
            cols = list(range(1,nc))
            df1 = pt_df[pt_df.columns[cols]]
            data_column = pd.DataFrame(df1.values.reshape(nr*(nc-1),1))#.astype(float)
            post_column = pd.DataFrame(pt_df[pt_df.columns[0]])
            post_column = np.repeat(post_column[post_column.columns[0]],nc-1).reset_index(drop=True)
            pre_column = list(pt_df)
            del pre_column[0]
            pre_column = pd.DataFrame(pre_column*nr)
            df_ret = pd.concat([post_column, pre_column, data_column],axis=1)
            df_ret.columns = range(df_ret.shape[1])
            return df_ret
        
        def refresh(self, df, astype=None):
            self.pt.set_dataframe(self.read_internal(df, astype), show_delete_row=False,\
                                  show_header=True, show_numbering=False, \
                                  first_column_is_id=True)
            self.pt.pack()
            
        def has_changed(self):
            return self.pt.has_changed()
      
    
    def raise_frame(frame):
        frame.tkraise()
    
    top_option_frame = tk.LabelFrame(root, text="File Management")
    table_frame = tk.LabelFrame(root, text="Connection Data")
    table_frame_internal = tk.Frame(table_frame)
    table_frame_controls = tk.Frame(table_frame)
    bottom_option_frame = tk.LabelFrame(root)
    
    top_option_frame.grid(column=0,row=0,sticky='we',padx=10,pady=5)
    table_frame.grid(column=0,row=1,sticky='we',padx=10,pady=5)
    table_frame_controls.grid(column=0, row=0, sticky='we')
    table_frame_internal.grid(column=0, row=1, sticky='news')
    bottom_option_frame.grid(column=0,row=2,sticky='we')
   
    page2 = tk.Frame(table_frame_internal)
    page3 = tk.Frame(table_frame_internal)
    page1 = tk.Frame(table_frame_internal)
    
    
    ######################################
        
    cellclasses_a = []
    options = glob.glob(connections_glob)
    
    d = defaultdict(list)
    d[1].append(cellclasses_a)
            
    
    tk.Button(table_frame_controls, text='Synaptic Weights', command=lambda:raise_frame(page1)).grid(column=0,row=0,padx=4,pady=4)
    text = 'Synaptic weight refers to the strength of a connection between two nodes, corresponding in biology to the influence the firing neuron on another neuron.'
    synaptic_weight_page_obj = connections_adapter(page1,2,text=text)
    
    tk.Button(table_frame_controls, text='Convergence', command=lambda:raise_frame(page2)).grid(column=1,row=0,padx=4,pady=4)
    text = 'Convergence defines the *total* number of connections to be randomly distributed between the presynaptic type and the postsynaptic type neuron.'
    convergence_page_obj = connections_adapter(page2,3,text)#convergence_page(page2)
    
    tk.Button(table_frame_controls, text='Synapses', command=lambda:raise_frame(page3)).grid(column=2,row=0,padx=4,pady=4)
    text = 'Synapses per connection to be made.'
    synapses_page_obj = connections_adapter(page3,4,text)#synapses_page(page3)
    
    
    ######################################
    
    
    def generate_files_available():
        cellclasses_a.clear()
        search = 'cells\\\\class_(.+?).hoc'
        for c in cellclasses:
            m = re.search(search, c)
            if m:
                cellclasses_a.append(m.group(1))
    
    def set_whole_df(df):
        page1.grid_forget()
        page2.grid_forget()
        page3.grid_forget()
        
        convergence_page_obj.refresh(df,'uint')
        synapses_page_obj.refresh(df,'uint')
        synaptic_weight_page_obj.refresh(df)
        
        page2.grid(column=0,row=0,sticky='news')
        page3.grid(column=0,row=0,sticky='news')
        page1.grid(column=0,row=0,sticky='news')
        
        return
    
    def load(*args,load_from=None):
        if not load_from:
            load_from = filename.get()
            
        df = pd.read_csv(load_from ,delimiter=' ',\
                       skiprows=1,header=None,\
                       names = ["Friendly Cell Name", "Cell File Name", "Num Cells", "Layer Index","Artificial:1 Real:0"])
        
        set_whole_df(df)
        
        display_app_status('Connections Data file \"'+filename.get()+'\" loaded')
        return
       
    def get_whole_df():
        wei_df = synaptic_weight_page_obj.get_df()
        con_df = convergence_page_obj.get_df()
        syn_df = synapses_page_obj.get_df()
        
        head_df = pd.DataFrame(wei_df[wei_df.columns[0:2]])
        
        wei_df = pd.DataFrame(wei_df[wei_df.columns[2]]).astype('float')
        wei_df.columns = [2]
        
        con_df = pd.DataFrame(con_df[con_df.columns[2]]).astype('float')
        con_df.columns = [3]
        
        syn_df = pd.DataFrame(syn_df[syn_df.columns[2]]).astype('float')
        syn_df.columns = [4]
        
        df = pd.concat([head_df, wei_df, con_df, syn_df],axis=1)
        
        return df
        
    def save(save_to=None):     
        
        if not save_to:
            save_to = filename.get()
        
        df = get_whole_df()
        (nr,nc) = df.shape
        tb = df.to_csv(sep=' ',header=False,index=False,float_format='%.6f')
                
        file = open(save_to,"w")
        file.write(str(nr)+'\n')
        file.write(tb)
        file.close()
        
        display_app_status('Connections Data file \"'+filename.get()+'\" saved')
        return
    
    def new():
        
        if synaptic_weight_page_obj.has_changed() or convergence_page_obj.has_changed() or synapses_page_obj.has_changed():  
            result = messagebox.askquestion("New", "Are you sure? Data has been changed.", icon='warning')
            if result != 'yes':
                return
        d = DialogEntryBox(root,text="New File Name:",lefttext=os.path.join(dataset_folder, conndata_file_prefix),righttext=conndata_file_postfix)
        root.wait_window(d.top)
        
        if d.confirm==False:
            return
        
        #get all as presynaptic
        #get all not artificial as postsynaptic
        
        newfilename = os.path.join(dataset_folder,conndata_file_prefix+ d.value.get() + conndata_file_postfix)

        loaded_cellnums = get_public_param("loaded_cellnums")
        
        column_names = ["Friendly Cell Name", "Cell File Name", "Num Cells", "Layer Index","Artificial:1 Real:0"]
        cellnums_pd = pd.read_csv(loaded_cellnums ,delimiter=' ',\
                       skiprows=1,header=None,\
                       names = column_names)
        
        cellnums_pd[column_names[4]] = cellnums_pd[column_names[4]].astype(int)
        
        pre = cellnums_pd[cellnums_pd.columns[0]].values.tolist()
        (pre_nr,pre_nc) = pd.DataFrame(pre).shape
        
        post = cellnums_pd.loc[cellnums_pd[column_names[4]] == 0]
        post = post[post.columns[0]]
        post = pd.DataFrame(post)
        (post_nr,post_nc) = post.shape
        
        post = np.repeat(post[post.columns[0]],pre_nr).reset_index(drop=True)
        pre = pd.DataFrame(pre*post_nr)
        
        df = pd.concat([post,pre],axis=1)
        df[2] = '0.0'
        df[3] = '0'
        df[4] = '0'
        
        tb = df.to_csv(sep=' ',header=False,index=False,float_format='%.6f')
                
        file = open(newfilename,"w")
        file.write(str(pre_nr*post_nr)+'\n')
        file.write(tb)
        file.close()
        
        load(load_from=newfilename)
        
        reload_files_and_set(newfilename)

        #create a presynaptic*postsynaptic by 5 pandas dataframe
        #set all values to zero
        #set first column
        #set second column
        
        display_app_status('Connections Data file \"'+filename.get()+'\" created')
        return
    
    def new_clone_current():
        
        if synaptic_weight_page_obj.has_changed() or convergence_page_obj.has_changed() or synapses_page_obj.has_changed():  
            result = messagebox.askquestion("New", "Are you sure? Data has been changed.", icon='warning')
            if result != 'yes':
                return
        d = DialogEntryBox(root,text="New File Name:",lefttext=os.path.join(dataset_folder, conndata_file_prefix),righttext=conndata_file_postfix)
        root.wait_window(d.top)
        
        if d.confirm==False:
            return
        
        
        newfilename = os.path.join(dataset_folder,conndata_file_prefix+ d.value.get() + conndata_file_postfix)
        f = open(newfilename,"w+")
        f.close()
        save(save_to=newfilename)
        
        reload_files_and_set()
        
        display_app_status('Connections Data file \"'+filename.get()+'\" was created')
        return
        
    
    def set_conndata_param():
        fn = filename.get()
        search = conndata_file_prefix+'(.+?)'+conndata_file_postfix
        m = re.search(search,fn)
        if m:
            fn = m.group(1)
        
        set_public_param("ConnData", fn)
        display_app_status('ConnData parameter set to \"'+ filename.get() +'\" in current parameters file')
        return

    def reload_files_and_set(newfilename):
        m = fileMenu.children['menu']
        m.delete(0,tk.END)
        newvalues = options
        newvalues.append(newfilename)
        for val in newvalues:
            m.add_command(label=val,command=lambda v=filename,l=val:v.set(l))
        filename.set(newfilename)
        
    def delete_current_file():
        return
        
    #generate_files_available()
    
    #Create the choice option panel
    filename = tk.StringVar(top_option_frame)
    filename.trace("w",load)
    
    conndat = get_public_param("ConnData")
    conndat = os.path.join(dataset_folder, conndata_file_prefix + conndat + conndata_file_postfix)
    filename.set(conndat)
    #filename.set(options[0])
    
    newFromCellsButton = tk.Button(top_option_frame, text="Generate New from Current Cells File", command=new, width=30)
    newFromCellsButton.grid(column=0, row =0, padx=5, sticky='WE',columnspan=1)
    useButton = tk.Button(top_option_frame, text="Set as ConnData parameter", command=set_conndata_param, width=30)
    useButton.grid(column=0, row =1, padx=5, sticky='W')
    
    fileMenu = tk.OptionMenu(top_option_frame, filename, *options)
    fileMenu.grid(column=1, row =0, padx=5, sticky='WE',columnspan=2)

    deleteButton = tk.Button(top_option_frame, text="Delete", command=delete_current_file)
    deleteButton.grid(column=3, row =0, padx=5, pady=5, sticky='W')
    deleteButton.config(state=tk.DISABLED)
    
    saveButton = tk.Button(top_option_frame, text="Save", command=save)
    saveButton.grid(column=1, row =1, padx=5,pady=5, sticky='WE')
    newFromCurrentButton = tk.Button(top_option_frame, text="Save As", command=new_clone_current)
    newFromCurrentButton.grid(column=2, row =1, padx=5, sticky='WE')
    
    
def synapses_page(root):
    sections_list = ['dendrite_list','soma_list','apical_list','axon_list']
    synapse_type_list = ['MyExp2Sid','ExpGABAab']
    condition_list = ['distance(x)','y3d(x)']
    synapse_column_names = ["Postsynaptic Cell", "Presynaptic Cells",\
                                "Synapse Type", "Postsynaptic Section Target",\
                                "Condition 1", "Condition 2",\
                                "Tau1a", "Tau2a", "ea",\
                                "Tau1b", "Tau2b", "eb"]
    class synapses_adapter(object):
        
        def __init__(self, root):
            self.root = root
            self.pt = PandasTable(self.root, show_add_row_button=False)
            self.pt.pack()
            
        def read_internal(self, df):
            '''get whole dataframe'''
            return df
        
        def get_df(self):
            df = self.pt.get_dataframe().replace(np.nan, '', regex=True).replace('nan','',regex=True)
            return df
        
        def refresh(self, df):
            d = defaultdict(list)
            d[3].append(sections_list)
            self.pt.set_dataframe(self.read_internal(df), show_delete_row=True,\
                                  show_header=True, show_numbering=True, \
                                  first_column_is_id=False, immutable_values=["nan"],\
                                  options_dict=d)
            self.pt.pack()
            
        def add_row(self, row):
            row = np.array(row).reshape(-1,len(row))
            r = pd.DataFrame(row,columns=synapse_column_names)
            
            for i, row in r.iterrows():
                self.pt.add_row(row)
                
            return
        
        def has_changed(self):
            return self.pt.has_changed()
        
    class SynapseEntryBox:
        def __init__(self, parent, text="value", lefttext="",righttext=""):
    
            top = self.top = tk.Toplevel(parent)
            top.geometry('475x450')
            top.resizable(0,0)
            tk.Label(top, text='Create new synapse:\nValues from currently loaded cells file.').grid(row=0,column=0,sticky="WE",columnspan=2)
            
            gaba_extras = tk.Frame(top)
            
            def showhide_gaba_extras(*args):
                if self.syntype_value.get() == synapse_type_list[1]:
                    gaba_extras.grid(row=10,column=0,columnspan=2)
                else:
                    gaba_extras.grid_forget()
                return
            
            self.pre_value = tk.StringVar(top)
            self.post_value = tk.StringVar(top)
            self.syntype_value = tk.StringVar(top)
            self.section_value = tk.StringVar(top)
            self.cond1_value = tk.StringVar(top)
            self.cond1_text_value = tk.StringVar(top)
            self.cond2_value = tk.StringVar(top)
            self.cond2_text_value = tk.StringVar(top)
            self.tau1a_value = tk.StringVar(top)
            self.tau2a_value = tk.StringVar(top)
            self.ea_value = tk.StringVar(top)
            self.tau1b_value = tk.StringVar(top)
            self.tau2b_value = tk.StringVar(top)
            self.eb_value = tk.StringVar(top)
            self.confirm = False
            
            #Inputs
            loaded_cellnums = get_public_param("loaded_cellnums")
            
            column_names = ["Friendly Cell Name", "Cell File Name", "Num Cells", "Layer Index","Artificial:1 Real:0"]
            cellnums_pd = pd.read_csv(loaded_cellnums ,delimiter=' ',\
                           skiprows=1,header=None,\
                           names = column_names)
            cellnums_pd[column_names[4]] = cellnums_pd[column_names[4]].astype(int)
            pre_options = cellnums_pd[cellnums_pd.columns[0]].values.tolist()
            post_options = cellnums_pd.loc[cellnums_pd[column_names[4]] == 0]
            post_options = post_options[post_options.columns[0]].values.tolist()
        
            
            l = tk.Label(top, text='Presynaptic Cell',width=25, background='light gray')
            l.grid(row=1,column=0,pady=5,padx=5)
            l.config(relief=tk.GROOVE)
            #self.pre = tk.Entry(top,textvariable=self.pre_value)
            self.pre = tk.OptionMenu(top, self.pre_value, *pre_options)
            self.pre.grid(row=1,column=1)
            
            l = tk.Label(top, text='Postsynaptic Cell',width=25, background='light gray')
            l.grid(row=2,column=0,pady=5,padx=5)
            l.config(relief=tk.GROOVE)
            #self.post = tk.Entry(top,textvariable=self.post_value)
            self.post = tk.OptionMenu(top, self.post_value, *post_options)
            self.post.grid(row=2,column=1)
            
            l = tk.Label(top, text='Synapse Type',width=25, background='light gray')
            l.grid(row=3,column=0,pady=5,padx=5)
            l.config(relief=tk.GROOVE)
            #self.syntype = tk.Entry(top,textvariable=self.syntype_value)
            self.syntype = tk.OptionMenu(top, self.syntype_value, *synapse_type_list)
            self.syntype_value.trace("w",showhide_gaba_extras)
            self.syntype_value.set(synapse_type_list[0])
            self.syntype.grid(row=3,column=1)
            
            l = tk.Label(top, text='Postsynaptic Section Target',width=25, background='light gray')
            l.grid(row=4,column=0,pady=5,padx=5)
            l.config(relief=tk.GROOVE)
            #self.section = tk.Entry(top,textvariable=self.section_value)
            self.section = tk.OptionMenu(top, self.section_value, *sections_list)
            self.section.grid(row=4,column=1)
            
            l = tk.Label(top, text='Condition 1',width=25, background='light gray')
            l.grid(row=5,column=0,pady=5,padx=5)
            l.config(relief=tk.GROOVE)
            #self.cond1 = tk.Entry(top,textvariable=self.cond1_value)
            self.cond1 = tk.OptionMenu(top, self.cond1_value, *condition_list)
            self.cond1_value.set(condition_list[0])
            self.cond1.grid(row=5,column=1)
            tk.Label(top, text=' > ').grid(row=5, column=2)
            self.cond1_text = tk.Entry(top, textvariable=self.cond1_text_value)
            self.cond1_text_value.set('-1')
            self.cond1_text.grid(row=5, column=3)
            
            
            l = tk.Label(top, text='Condition 2',width=25, background='light gray')
            l.grid(row=6,column=0,pady=5,padx=5)
            l.config(relief=tk.GROOVE)
            #self.cond2 = tk.Entry(top,textvariable=self.cond2_value)
            self.cond2 = tk.OptionMenu(top, self.cond2_value, *condition_list)
            self.cond2_value.set(condition_list[0])
            self.cond2.grid(row=6,column=1)
            tk.Label(top, text=' < ').grid(row=6, column=2)
            self.cond2_text = tk.Entry(top, textvariable=self.cond2_text_value)
            self.cond2_text_value.set('10000')
            self.cond2_text.grid(row=6, column=3)
            
            l = tk.Label(top, text='Tau1a',width=25, background='light gray')
            l.grid(row=7,column=0,pady=5,padx=5)
            l.config(relief=tk.GROOVE)
            self.tau1a = tk.Entry(top,textvariable=self.tau1a_value)
            self.tau1a_value.set('2.0')
            self.tau1a.grid(row=7,column=1)
            
            l = tk.Label(top, text='Tau2a',width=25, background='light gray')
            l.grid(row=8,column=0,pady=5,padx=5)
            l.config(relief=tk.GROOVE)
            self.tau2a = tk.Entry(top,textvariable=self.tau2a_value)
            self.tau2a_value.set('6.3')
            self.tau2a.grid(row=8,column=1)
            
            l = tk.Label(top, text='ea',width=25, background='light gray')
            l.grid(row=9,column=0,pady=5,padx=5)
            l.config(relief=tk.GROOVE)
            self.ea = tk.Entry(top,textvariable=self.ea_value)
            self.ea_value.set('0.0')
            self.ea.grid(row=9,column=1)
            
            
            
            l = tk.Label(gaba_extras, text='Tau1b',width=25, background='light gray')
            l.grid(row=10,column=0,pady=5,padx=5)
            l.config(relief=tk.GROOVE)
            self.tau1b = tk.Entry(gaba_extras,textvariable=self.tau1b_value)
            self.tau1b.grid(row=10,column=1)
            
            l = tk.Label(gaba_extras, text='Tau2b',width=25, background='light gray')
            l.grid(row=11,column=0,pady=5,padx=5)
            l.config(relief=tk.GROOVE)
            self.tau2b = tk.Entry(gaba_extras,textvariable=self.tau2b_value)
            self.tau2b.grid(row=11,column=1)
            
            l = tk.Label(gaba_extras, text='eb',width=25, background='light gray')
            l.grid(row=12,column=0,pady=5,padx=5)
            l.config(relief=tk.GROOVE)
            self.eb = tk.Entry(gaba_extras,textvariable=self.eb_value)
            self.eb.grid(row=12,column=1)
            
            
            #Return
            
            button_frame = tk.Frame(top)
            button_frame.grid(row=20,column=0,columnspan=2)
            
            b = tk.Button(button_frame, text="Ok", command=self.ok)
            b.grid(pady=5, padx=5, column=0, row=0, sticky="WE")
            
            b = tk.Button(button_frame, text="Cancel", command=self.cancel)
            b.grid(pady=5, padx=5, column=1, row=0, sticky="WE")
            
        def verify_good(self):
            return True
    
        def get_values(self):
            if self.syntype_value.get() == synapse_type_list[0]: #set to nan if it's not a gabaab
                self.tau1b_value.set('nan')
                self.tau2b_value.set('nan')
                self.eb_value.set('nan')
                
            newsyn = [self.pre_value.get(), self.post_value.get(), self.syntype_value.get(),
                  self.section_value.get(), self.cond1_value.get()+'>'+self.cond1_text_value.get(), self.cond2_value.get()+'<'+self.cond2_text_value.get(),
                  self.tau1a_value.get(), self.tau2a_value.get(), self.ea_value.get(),
                  self.tau1b_value.get(), self.tau2b_value.get(), self.eb_value.get()]
            return newsyn
            
        def ok(self):
            self.confirm = True
            self.top.destroy()
        def cancel(self):
            self.top.destroy()
      
    
    def add_synapse(*args):
        d = SynapseEntryBox(root)
        root.wait_window(d.top)
        
        if d.confirm==False:
            return
        if d.verify_good():
            synapses_page_obj.add_row(d.get_values())
    
    top_option_frame = tk.LabelFrame(root, text="File Management")
    table_frame = tk.LabelFrame(root, text="Synapse Data")
    table_frame_internal = tk.Frame(table_frame)
    table_frame_controls = tk.Frame(table_frame)
    bottom_option_frame = tk.LabelFrame(root)
    
    bottom_option_frame.tk
    
    top_option_frame.grid(column=0,row=0,sticky='we',padx=10,pady=5)
    table_frame.grid(column=0,row=1,sticky='we',padx=10,pady=5)
    table_frame_controls.grid(column=0, row=0, sticky='we')
    table_frame_internal.grid(column=0, row=1, sticky='news')
    bottom_option_frame.grid(column=0,row=2,sticky='we')
   
    
    page1 = tk.Frame(table_frame_internal) 
    
    ######################################
    
    cellclasses_a = []
    options = glob.glob(syndata_glob)
    
    d = defaultdict(list)
    d[1].append(cellclasses_a)
    
    tk.Button(table_frame_controls, text='Add Synapse Type', command=add_synapse).grid(column=0,row=0, padx=5, pady=5)
    synapses_page_obj = synapses_adapter(page1)
    
    ######################################
    
    
    def generate_files_available():
        cellclasses_a.clear()
        search = 'cells\\\\class_(.+?).hoc'
        for c in cellclasses:
            m = re.search(search, c)
            if m:
                cellclasses_a.append(m.group(1))
    
    def load(*args):
        #print ("loading: " + filename.get())
        df = pd.read_csv(filename.get() ,delim_whitespace=True,\
                       skiprows=1,header=None,\
                       names = synapse_column_names)
        cols = list(df.columns.values) #switch pre and post synaptic 
        cols.insert(0, cols.pop(1))
        df = df[cols]
        
        
        page1.grid_forget()
        synapses_page_obj.refresh(df)
        page1.grid(column=0,row=0,sticky='news')
        
        display_app_status('Synapse Data file \"'+filename.get()+'\" loaded')
       
    def save(save_to=None):
        pt_df = synapses_page_obj.get_df()
        
        cols = list(pt_df.columns.values) #switch pre and post synaptic 
        cols.insert(0, cols.pop(1))
        pt_df = pt_df[cols]
        
        (nr,nc) = pt_df.shape 
        
        #a = pd.DataFrame(pt_df[pt_df.columns[list(range(0,6))]])
        #b = pd.DataFrame(pt_df[pt_df.columns[list(range(6,12))]]).astype('float')
        #pt_df = pd.concat([a,b],axis=1)
        
        tb = pt_df.to_csv(sep=' ',header=False,index=False,float_format='%.6f')
        
        if not save_to:
            save_to=filename.get()
        
        file = open(save_to,"w")
        file.write(str(nr)+'\n')
        file.write(tb)
        file.close()
        display_app_status('Synapse Data file \"'+filename.get()+'\" saved')
        
        return
    
    def new():
        if synapses_page_obj.has_changed():
            result = messagebox.askquestion("New", "Are you sure? Data has been changed.", icon='warning')
            if result != 'yes':
                return
        d = DialogEntryBox(root,text="New File Name:",lefttext=os.path.join(dataset_folder, syndata_file_prefix),righttext=syndata_file_postfix)
        root.wait_window(d.top)
        
        if d.confirm==False:
            return
        
        newfilename = dataset_folder+'\\'+syndata_file_prefix+ d.value.get() + syndata_file_postfix
        f = open(newfilename,"w+")
        f.close
        #pt.new()
        #generate_files_available()
        ##https://stackoverflow.com/questions/17580218/changing-the-options-of-a-optionmenu-when-clicking-a-button
    
        m = fileMenu.children['menu']
        m.delete(0,tk.END)
        newvalues = options
        newvalues.append(newfilename)
        for val in newvalues:
            m.add_command(label=val,command=lambda v=filename,l=val:v.set(l))
        filename.set(newfilename)
        
        #pt.new()
        display_app_status('Synapse Data file \"'+filename.get()+'\" created')
        return

    def new_clone_current():
        
        if synapses_page_obj.has_changed():  
            result = messagebox.askquestion("New", "Are you sure? Data has been changed.", icon='warning')
            if result != 'yes':
                return
        d = DialogEntryBox(root,text="New File Name:",lefttext=os.path.join(dataset_folder, syndata_file_prefix),righttext=syndata_file_postfix)
        root.wait_window(d.top)
        
        if d.confirm==False:
            return
        
        
        newfilename = os.path.join(dataset_folder,syndata_file_prefix+ d.value.get() + syndata_file_postfix)
        f = open(newfilename,"w+")
        f.close()
        save(save_to=newfilename)
        
        m = fileMenu.children['menu']
        m.delete(0,tk.END)
        newvalues = options
        newvalues.append(newfilename)
        for val in newvalues:
            m.add_command(label=val,command=lambda v=filename,l=val:v.set(l))
        filename.set(newfilename)
        
        display_app_status('Synapse Data file \"'+filename.get()+'\" was created')
        return
        

    def set_syndata_param():
        fn = filename.get()
        search = syndata_file_prefix+'(.+?)'+syndata_file_postfix
        m = re.search(search,fn)
        if m:
            fn = m.group(1)
        
        set_public_param("SynData", fn)
        display_app_status('SynData parameter set to \"'+ filename.get() +'\" in current parameters file')
        return
    
    def delete_current_file():
        return
    
    #generate_files_available()
    
    #Create the choice option panel
    filename = tk.StringVar(top_option_frame)
    filename.trace("w",load)
    
    syndat = get_public_param("SynData")
    syndat = os.path.join(dataset_folder, syndata_file_prefix + syndat + syndata_file_postfix)
    filename.set(syndat)
    
    #filename.set(options[0])
    
    newFromCellsButton = tk.Button(top_option_frame, text="Create New", command=new, width=30)
    newFromCellsButton.grid(column=0, row =0, padx=5, sticky='WE')
    useButton = tk.Button(top_option_frame, text="Set as SynData parameter", command=set_syndata_param, width=30)
    useButton.grid(column=0, row =1, padx=5, sticky='W')
        
    fileMenu = tk.OptionMenu(top_option_frame, filename, *options)
    fileMenu.grid(column=1, row =0, padx=5, sticky='WE', columnspan=2)
    
    deleteButton = tk.Button(top_option_frame, text="Delete", command=delete_current_file)
    deleteButton.grid(column=3, row =0, padx=5, pady=5, sticky='W')
    deleteButton.config(state=tk.DISABLED)
    
    saveButton = tk.Button(top_option_frame, text="Save", command=save)
    saveButton.grid(column=1, row =1, padx=5, pady=5, sticky='WE')
    newFromCurrentButton = tk.Button(top_option_frame, text="Save As", command=new_clone_current)
    newFromCurrentButton.grid(column=2, row =1, padx=5, sticky='WE')
    

    return

def phasic_page(root):
           
    phase_column_list = ["Cell","Max Frequency (Hz)","Noise","Depth","Phase"]
    
    top_option_frame = tk.LabelFrame(root, text="File Management")
    table_frame = tk.LabelFrame(root, text="Phasic Stimulation")
    table_frame_internal = tk.Frame(table_frame)
    table_frame_controls = tk.Frame(table_frame)
    bottom_option_frame = tk.LabelFrame(root)
    
    bottom_option_frame.tk
    
    top_option_frame.grid(column=0,row=0,sticky='we',padx=10,pady=5)
    table_frame.grid(column=0,row=1,sticky='we',padx=10,pady=5)
    table_frame_controls.grid(column=0, row=0, sticky='we')
    table_frame_internal.grid(column=0, row=1, sticky='news')
    bottom_option_frame.grid(column=0,row=2,sticky='we')
   
    
    page1 = tk.Frame(table_frame_internal)    
    
    ######################################
    
    cellclasses_a = []
    options = glob.glob(phasicdata_glob)
    
    d = defaultdict(list)
    d[1].append(cellclasses_a)

    ######################################
    pt = PandasTable(table_frame_internal, show_add_row_button=False)
    
    
    class PhasicEntryBox:
        def __init__(self, parent, text="value", lefttext="",righttext=""):
    
            top = self.top = tk.Toplevel(parent)
            top.geometry('325x250')
            top.resizable(0,0)
            tk.Label(top, text='Enter new phasic stimulation information:\nCell types from currently loaded \ncells file artificial cells.').grid(row=0,column=0,sticky="WE",columnspan=2)
            
            
            self.cell_value = tk.StringVar(top)
            self.frequency_value = tk.StringVar(top)
            self.noise_value = tk.StringVar(top)
            self.depth_value = tk.StringVar(top)
            self.phase_value = tk.StringVar(top)
            self.confirm = False
            
            #Inputs
            loaded_cellnums = get_public_param("loaded_cellnums")
            
            column_names = ["Friendly Cell Name", "Cell File Name", "Num Cells", "Layer Index","Artificial:1 Real:0"]
            cellnums_pd = pd.read_csv(loaded_cellnums ,delimiter=' ',\
                           skiprows=1,header=None,\
                           names = column_names)
            cellnums_pd[column_names[4]] = cellnums_pd[column_names[4]].astype(int)
            post_options = cellnums_pd.loc[cellnums_pd[column_names[4]] != -1]
            post_options = post_options[post_options.columns[0]].values.tolist()
            
            l = tk.Label(top, text='Cell',width=25, background='light gray')
            l.grid(row=2,column=0,pady=5,padx=5)
            l.config(relief=tk.GROOVE)
            #self.post = tk.Entry(top,textvariable=self.post_value)
            self.cell = tk.OptionMenu(top, self.cell_value, *post_options)
            self.cell.grid(row=2,column=1)

            
            l = tk.Label(top, text='Max Frequency (Hz)',width=25, background='light gray')
            l.grid(row=3,column=0,pady=5,padx=5)
            l.config(relief=tk.GROOVE)
            self.frequency = tk.Entry(top,textvariable=self.frequency_value)
            self.frequency_value.set('1')
            self.frequency.grid(row=3,column=1)
            
            l = tk.Label(top, text='Noise',width=25, background='light gray')
            l.grid(row=4,column=0,pady=5,padx=5)
            l.config(relief=tk.GROOVE)
            self.noise = tk.Entry(top,textvariable=self.noise_value)
            self.noise_value.set('0.0')
            self.noise.grid(row=4,column=1)
            
            l = tk.Label(top, text='Depth',width=25, background='light gray')
            l.grid(row=5,column=0,pady=5,padx=5)
            l.config(relief=tk.GROOVE)
            self.depth = tk.Entry(top,textvariable=self.depth_value)
            self.depth_value.set('0.0')
            self.depth.grid(row=5,column=1)
            
            l = tk.Label(top, text='Phase',width=25, background='light gray')
            l.grid(row=6,column=0,pady=5,padx=5)
            l.config(relief=tk.GROOVE)
            self.phase = tk.Entry(top,textvariable=self.phase_value)
            self.phase_value.set('0')
            self.phase.grid(row=6,column=1)
            
            #Return
            
            button_frame = tk.Frame(top)
            button_frame.grid(row=20,column=0,columnspan=2)
            
            b = tk.Button(button_frame, text="Ok", command=self.ok)
            b.grid(pady=5, padx=5, column=0, row=0, sticky="WE")
            
            b = tk.Button(button_frame, text="Cancel", command=self.cancel)
            b.grid(pady=5, padx=5, column=1, row=0, sticky="WE")
            
        def verify_good(self):
            return True
    
        def get_values(self):
            newphase = [self.cell_value.get(), self.frequency_value.get(), self.noise_value.get(),
                  self.depth_value.get(), self.phase_value.get()]
            return newphase
            
        def ok(self):
            self.confirm = True
            self.top.destroy()
        def cancel(self):
            self.top.destroy()
    
    def generate_files_available():
        cellclasses_a.clear()
        search = 'cells\\\\class_(.+?).hoc'
        for c in cellclasses:
            m = re.search(search, c)
            if m:
                cellclasses_a.append(m.group(1))
    
    def load(*args):
        
        df = pd.read_csv(filename.get() ,delim_whitespace=True,\
                       skiprows=1,header=None,\
                       names = phase_column_list)
        
        pt.pack()
        pt.set_dataframe(df, show_delete_row=True,\
                                  show_header=True, show_numbering=True, \
                                  first_column_is_id=False, immutable_values=["nan"])
        
        display_app_status('Phasic Data file \"'+filename.get()+'\" loaded')
       
    def save(save_to=None):
        pt_df = pt.get_dataframe()
        (nr,nc) = pt_df.shape 
        tb = pt_df.to_csv(sep=' ',header=False,index=False)
        
        if not save_to:
            save_to = filename.get()
        
        file = open(save_to,"w")
        file.write(str(nr)+'\n')
        file.write(tb)
        file.close()
        display_app_status('Phasic Data file \"'+filename.get()+'\" saved')
        return
    
    def new_generate():
        newfilename = ''
        if pt.has_changed():
            result = messagebox.askquestion("New", "Are you sure? Data has been changed.", icon='warning')
            if result != 'yes':
                return
        d = DialogEntryBox(root,text="New File Name:",lefttext=os.path.join(dataset_folder, phasicdata_file_prefix),righttext=phasicdata_file_postfix)
        root.wait_window(d.top)
        
        if d.confirm==False:
            return
        
        newfilename = dataset_folder+'\\'+phasicdata_file_prefix+ d.value.get() + phasicdata_file_postfix
        f = open(newfilename,"w+")
        f.close
        #pt.new()
        #generate_files_available()
        #https://stackoverflow.com/questions/17580218/changing-the-options-of-a-optionmenu-when-clicking-a-button
    
        m = fileMenu.children['menu']
        m.delete(0,tk.END)
        newvalues = options
        newvalues.append(newfilename)
        for val in newvalues:
            m.add_command(label=val,command=lambda v=filename,l=val:v.set(l))
        filename.set(newfilename)
        
        #pt.new()
        display_app_status('Phasic Data file \"'+ newfilename +'\" created')
        return
    
    def new_clone_current():
        
        if pt.has_changed():  
            result = messagebox.askquestion("New", "Are you sure? Data has been changed.", icon='warning')
            if result != 'yes':
                return
        d = DialogEntryBox(root,text="New File Name:",lefttext=os.path.join(dataset_folder, phasicdata_file_prefix),righttext=phasicdata_file_postfix)
        root.wait_window(d.top)
        
        if d.confirm==False:
            return
        
        
        newfilename = os.path.join(dataset_folder,phasicdata_file_prefix+ d.value.get() + phasicdata_file_postfix)
        f = open(newfilename,"w+")
        f.close()
        save(save_to=newfilename)
        
        m = fileMenu.children['menu']
        m.delete(0,tk.END)
        newvalues = options
        newvalues.append(newfilename)
        for val in newvalues:
            m.add_command(label=val,command=lambda v=filename,l=val:v.set(l))
        filename.set(newfilename)
        
        display_app_status('Phasic Data file \"'+filename.get()+'\" was created')
        return

    def set_phasicdata_param():
        fn = filename.get()
        search = phasicdata_file_prefix+'(.+?)'+phasicdata_file_postfix
        m = re.search(search,fn)
        if m:
            fn = m.group(1)
        set_public_param("PhasicData", fn)
        display_app_status('PhasicData parameter set to \"'+ filename.get() +'\" in current parameters file')
        return

    #generate_files_available()
    
    def add_phase(*args):
        d = PhasicEntryBox(root)
        root.wait_window(d.top)
        
        if d.confirm==False:
            return
        if d.verify_good():
            row = d.get_values()
            row = np.array(row).reshape(-1,len(row))
            r = pd.DataFrame(row,columns=phase_column_list)
            
            for i, row in r.iterrows():
                pt.add_row(row)
    
    def delete_current_file():
        return
    
    
    tk.Button(table_frame_controls, text='Add Phasic Stimulus', command=add_phase).grid(column=0,row=0, padx=5, pady=5)
    
    
    #Create the choice option panel
    filename = tk.StringVar(top_option_frame)
    filename.trace("w",load)
    
    phasicdat = get_public_param("PhasicData")
    phasicdat = os.path.join(dataset_folder, phasicdata_file_prefix + phasicdat + phasicdata_file_postfix)
    filename.set(phasicdat)
    #filename.set(options[0])
    
    newFromCellsButton = tk.Button(top_option_frame, text="Create New", command=new_generate, width=30)
    newFromCellsButton.grid(column=0, row =0, padx=5, sticky='WE')
    useButton = tk.Button(top_option_frame, text="Set as PhasicData parameter", command=set_phasicdata_param, width=30)
    useButton.grid(column=0, row =1, padx=5, sticky='W')
        
    fileMenu = tk.OptionMenu(top_option_frame, filename, *options)
    fileMenu.grid(column=1, row =0, padx=5, sticky='WE', columnspan=2)
    
    deleteButton = tk.Button(top_option_frame, text="Delete", command=delete_current_file)
    deleteButton.grid(column=3, row =0, padx=5, pady=5, sticky='W')
    deleteButton.config(state=tk.DISABLED)
    
    saveButton = tk.Button(top_option_frame, text="Save", command=save)
    saveButton.grid(column=1, row =1, padx=5, pady=5, sticky='WE')
    newFromCurrentButton = tk.Button(top_option_frame, text="Save As", command=new_clone_current)
    newFromCurrentButton.grid(column=2, row =1, padx=5, sticky='WE')

    return

def results_page(root):
        
    buildrun_frame = tk.LabelFrame(root, text="Run Model")
    results_frame = tk.LabelFrame(root, text="General Results")
    console_frame = tk.LabelFrame(root, text="Console Output")
        
    buildrun_frame.grid(column=0,row=0,sticky='NEWS',padx=10,pady=5)
    results_frame.grid(column=0,row=1,sticky='NEWS',padx=10,pady=5)
    console_frame.grid(column=1, row=0, rowspan=2, sticky='NEWS')
    
    #######Build Section
    ##############################
    
    def reload_results():   
        options = glob.glob(results_glob)
        m = fileMenu.children['menu']
        m.delete(0,tk.END)
        newvalues = options
        for val in newvalues:
            m.add_command(label=val,command=lambda v=foldername,l=val:v.set(l))
        return
    
    def run_command(command):
        try:
            p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return iter(p.stdout.readline, b'')
        except Exception as e:
            return iter(str(e).splitlines())

    def run_command_in_console(command):
        console.configure(state='normal')
        console.insert('end', 'console > ' + command + '\n\n')
        command = command.split()
        for line in run_command(command):
            try:
                string = line.decode('unicode_escape')
            except Exception:
                string = line
            console.insert('end', '' + string)
            console.see(tk.END)
        console.insert('end', 'console > \n')
        console.configure(state='disabled')
        #display_app_status('Not implemented')
        reload_results()
        return
    #TODO THREADING IS A WIP, need to convert everything to classes first to ensure we only run 1 at a time
    def run_command_in_console_threaded(command):
        import threading
        t1 = threading.Thread(target=lambda r=command:run_command_in_console(r))
        t1.start()
        return
    
        
    def generate_batch():
        #Create popup with questions for batch, with defaults loaded from json file
        display_app_status('Not implemented')
        return
    
    def build_run_batch():
        generate_batch()
        
    
    def local_run():
        run = 'nrniv main.hoc'
        run_command_in_console_threaded(run)
        return
    
    buildButton = tk.Button(buildrun_frame, text="Build Parallel Batch", command=generate_batch)
    buildButton.grid(column=0, row =0, padx=5, pady=5, sticky='WE')
    buildButton.config(state=tk.DISABLED)
    
    buildrunButton = tk.Button(buildrun_frame, text="Build & Run Parallel Batch", command=build_run_batch)
    buildrunButton.grid(column=0, row =1, padx=5, pady=5, sticky='WE')
    buildrunButton.config(state=tk.DISABLED)
    
    localrunButton = tk.Button(buildrun_frame, text="Run on this Single Machine", command=local_run)
    localrunButton.grid(column=2, row =0, padx=5, pady=5, sticky='WE')
    
    #I envision this button to open a popup to configure a remote connection, sftp all files in this directory
    #Maybe treating this as a git repository, some sort of version control, so we can copy the results back to 
    #this system, may be a huge pain to implement/not worth it
    buildrunButton = tk.Button(buildrun_frame, text="Run on Remote System (SSH)", command=build_run_batch)
    buildrunButton.grid(column=2, row =1, padx=5, pady=5, sticky='WE')
    buildrunButton.config(state=tk.DISABLED)
    
    ##############################
    
    
    ######Results section
    ##############################
    
    class ShowGraphBox:
        def __init__(self, parent, df, plottype='line', text="Graph Area"):
    
            top = self.top = tk.Toplevel(parent)
            top.geometry('510x430')
            top.resizable(0,0)
            #tk.Label(top, text='Create new synapse:').grid(row=0,column=0,sticky="WE",columnspan=2)
            lf = ttk.Labelframe(top, text=text)
            lf.grid(row=4, column=0, sticky='nwes', padx=3, pady=3)
            
            fig = Figure(figsize=(5,4), dpi=100)
            ax = fig.add_subplot(111)
            
            #df.plot(x='t', y='s', ax=ax)
            df.plot(kind=plottype, ax=ax)
            canvas = FigureCanvasTkAgg(fig, master=lf)
            canvas.show()
            canvas.get_tk_widget().grid(row=0, column=0)
        
    def generate_spike_raster():
        display_app_status('Not implemented')
        return
    selected = {}
    #selected = ['trace_hco10.dat', 'trace_hco21.dat']
    def display_spike_train():
       
        if not bool(selected): #nothing selected
            display_app_status('Nothing selected, stopping')
            return
        
        cells_v = {}
        #for fn in selected:
        for fn, value in selected.items():
            #filename = os.path.join(foldername.get(), fn)
            if value.get() is 0:
                continue
            df = pd.read_csv(fn ,delim_whitespace=True,\
                           skiprows=1,header=None,\
                           names = ['Time', 'voltage'])
            cellname = ''
            search = 'trace_(.+?).dat'
            m = re.search(search,fn)
            if m:
                cellname = m.group(1)
            cells_v[cellname] = list(df['voltage'])
        
        #print(cells_v)
        df_p = pd.DataFrame(cells_v, index=df['Time'])
        
        ShowGraphBox(results_frame, df_p)
        return

    
    def load_results(*args):
        selected.clear()
        
        for widget in cellslistbox.winfo_children():
            widget.destroy()
        results_trace_glob = os.path.join(foldername.get(),trace_file_prefix + '*' + trace_file_postfix)
        available_traces = glob.glob(results_trace_glob)
                
        for i,trace in enumerate(available_traces):
            var1 = tk.IntVar()
            selected[trace] = var1
            tk.Checkbutton(cellslistbox, text=trace, variable=var1).grid(row=i, sticky='w')
        return
        
        
    result_options = glob.glob(results_glob)
    foldername = tk.StringVar(results_frame)
    foldername.set('')#result_options[0])
    foldername.trace("w",load_results)
    
    
    
    r = tk.Label(results_frame,text='Results loaded: ')
    r.grid(column=0, row =0)
    
    fileMenu = tk.OptionMenu(results_frame, foldername, *result_options)
    fileMenu.grid(column=1, row =0, padx=5, sticky='WE', columnspan=2)
    
    cellslistbox = tk.LabelFrame(results_frame, text='Cell Traces')
    cellslistbox.grid(column=0,row=1,padx=5,sticky='WE',rowspan=99)
        
    spikerasterButton = tk.Button(results_frame, text="Show Spike Raster for all", command=generate_spike_raster)
    spikerasterButton.grid(column=1, row =1, padx=5, pady=5, sticky='WE')
    spikerasterButton.config(state=tk.DISABLED)
    
    graphspikeButton = tk.Button(results_frame, text="Show Spike Activity for selected", command=display_spike_train)
    graphspikeButton.grid(column=1, row =2, padx=5, pady=5, sticky='WE')
    
    ##############################
    
    ######Console section
    ##############################
    
    c = tk.Label(console_frame,text='Live output for current run.')
    c.grid(column=0, row=0)
    
    console = tk.Text(console_frame)
    console.config(width= 70, height=25, bg='black',fg='light green')
    console.grid(column=0, row=1, padx=5, pady=5, sticky='NEWS')
    
    console.configure(state='normal')
    console.insert('end', 'console > \n')
    console.configure(state='disabled')
    
    ##############################
    return

def main(root):
    
    
    style = ttk.Style()
    try:
        style.theme_create( "colored", parent="alt", settings={
                "TNotebook": {"configure": {"tabmargins": [2, 5, 2, 0] } },
                "TNotebook.Tab": {
                    "configure": {"padding": [5, 2], "background": "#D9D9D9" },
                    "map":       {"background": [("selected", "#C0C0E0")],
                                  "expand": [("selected", [1, 1, 1, 0])] } } } )
    
        style.theme_create( "largertheme", parent="alt", settings={
                "TNotebook": {"configure": {"tabmargins": [2, 5, 2, 0] } },
                "TNotebook.Tab": {
                    "configure": {"padding": [5, 2] },
                    "map":       {
                                  "expand": [("selected", [1, 1, 1, 0])] } } } )
        style.theme_use("colored")
    except Exception:
        print('style already loaded')
    
    frame1 = tk.Frame(root)
    frame1.grid(row=0,column=0,sticky='news')
    frame1.columnconfigure(0,weight=1)
    frame1.columnconfigure(0,weight=1)
    frame2 = tk.Frame(root)
    frame2.grid(row=1,column=0,sticky='news')
    
    nb = Autoresized_Notebook(frame1)
    nb.pack(padx=5,pady=5,side="left",fill="both",expand=True)
    
    bottom_status_bar = tk.Frame(frame2)
    bottom_status_bar.grid(row=0,column=0,padx=5,pady=2)#,fill=tk.X,expand=True)
    
    label = tk.Label(bottom_status_bar,textvariable=app_status)
    label.pack(expand=True)

    page1 = ttk.Frame(nb)
    page2 = ttk.Frame(nb)
    page3 = ttk.Frame(nb)
    page4 = ttk.Frame(nb)
    page5 = ttk.Frame(nb)
    page6 = ttk.Frame(nb)
    page7 = ttk.Frame(nb)
    page8 = ttk.Frame(nb)
    
    nb.add(page1, text='Network Model Builder')
    nb.add(page2, text='Cells')
    nb.add(page3, text='Connections')
    nb.add(page4, text='Synapses')
    nb.add(page5, text='Phasic Stimulation')
    #nb.add(page6, text='Cell Builder')
    #nb.add(page7, text='Ion Channel Builder')
    nb.add(page8, text='Run & Display Results')
    
    #Alternatively you could do parameters_page(page1), but wouldn't get scrolling
    bind_page(page1, parameters_page)
    bind_page(page2, cells_page)
    bind_page(page3, connections_page)
    bind_page(page4, synapses_page)
    bind_page(page5, phasic_page)
    bind_page(page8, results_page)
    
    display_app_status("Ready")
    try:
        print('Starting Sim Builder')
        root.mainloop()
    except Exception:
        print('Error, closing display loop')
    print('Closing Sim Builder')

default_status = "Status: Ready"
def reset_app_status():
    app_status.set(default_status)

def display_app_status(str):
    app_status.set("Status: "+str)
    threading.Timer(4.0, reset_app_status).start()
            
root.columnconfigure(0,weight=1)
root.rowconfigure(0,weight=1)
root.title("Generalized Neuron Network Model Builder (University of Missouri - Neural Engineering Laboratory - Nair) BETA VERSION")
root.geometry('1050x600')

#root.resizable(0,0)
root.config(menu=menu_bar(root))

app_status = tk.StringVar(root,'')
reset_app_status()

main(root)
