# -*- coding: utf-8 -*-
"""
Created on Wed May 16 10:53:53 2018
@author: tjbanks
"""

from cx_Freeze import setup, Executable
import matplotlib
from matplotlib.backends import backend_qt5agg
import os

os.environ['TCL_LIBRARY'] = r'C:\Users\Tyler\Anaconda3\tcl\tcl8.6'
os.environ['TK_LIBRARY'] = r'C:\Users\Tyler\Anaconda3\tcl\tk8.6'

base = "Win32GUI"    

#path_platforms = ( "C:\\Users\\Tyler\\Anaconda3\\pkgs\\qt-5.9.5-vc14he4a7d60_0\\Library\\plugins\\platforms\\qwindows.dll", "platforms\qwindows.dll" )

executables = [Executable("sim_builder.py", base=base)]

packages = ["idna","time","re","subprocess","threading","tempfile","shutil","os","random","numpy","pandas","paramiko","getpass","zipfile","tkinter","tarfile","matplotlib.backends.backend_qt5agg"]
includes = ["atexit","PyQt5.QtCore","PyQt5.QtGui", "PyQt5.QtWidgets", "numpy", "numpy.core._methods"]
#includefiles = [path_platforms]
options = {
    'build_exe': {    
        'includes': includes,
#        'include_files': includefiles,
        'packages':packages,
        "include_files":[(matplotlib.get_data_path(), "mpl-data")]
    },    
}

setup(
    name = "Sim Builder",
    options = options,
    version = "1",
    description = 'Sim Builder - University of Missouri - Nair Lab (Tyler Banks)',
    executables = executables
)