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


class CreateToolTip(object):
    """
    create a tooltip for a given widget
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
               line_option = re.search(',(.+?)$', m.group(1))
               line_comment = re.search('\/\/ (.+?)$',line)
                   
               temp = tk.Label(frame, text=line_text.group(1))
               #temp.pack()
               temp.grid(column=0, row =r, padx=5, sticky='W') 
               
               
               e = tk.Entry(frame)
               e.delete(0,tk.END)
               e.insert(0,line_option.group(1))
               #e.pack()
               e.grid(column=1, row=r, sticky='E')
               
               CreateToolTip(temp,line_comment.group(1))
               
               #temp = tk.Label(frame, text=)
               #temp.pack()
               #temp.grid(column=2, row =r, sticky='W') 
                          
               r = r+1
           line = fp.readline()
           cnt += 1

def cells_page(frame):
    height = 5
    width = 5
    for i in range(height): #Rows
        for j in range(width): #Columns
            b = tk.Entry(frame, text="",relief=tk.RIDGE)
            b.grid(row=i, column=j)


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
    
    nb.add(page1, text='Parameters')
    nb.add(page2, text='Cells')
    nb.add(page3, text='Connections')
    nb.add(page4, text='Synapses')
    nb.add(page5, text='Phasic Data')
    
    #Alternatively you could do parameters_page(page1), but wouldn't get scrolling
    bind_page(page1, parameters_page)
    bind_page(page2, cells_page)
    
    root.mainloop()

main()