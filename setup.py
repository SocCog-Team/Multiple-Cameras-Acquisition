from cx_Freeze import setup, Executable

import os.path
PYTHON_INSTALL_DIR = os.path.dirname(os.path.dirname(os.__file__))
os.environ['TCL_LIBRARY'] = os.path.join(PYTHON_INSTALL_DIR, 'tcl', 'tcl8.6')
os.environ['TK_LIBRARY'] = os.path.join(PYTHON_INSTALL_DIR, 'tcl', 'tk8.6')

base = None    

executables = [Executable("test.py", base=base)]

packages = ["idna", "data_structures", "acquisition_ini", "numpy", "mkl", "wx", "PIL", "datetime", "threading", "time", "SpinnakerCamera", "VideoAcquisitionThread", "VideoProcessingThread", "wxWindow", "main_control_window", "SpinnakerControl", "VideoSingleton", "collections", "PySpin"]
options = {
    'build_exe': {    
        'packages':packages,
        'include_files':[
            os.path.join(PYTHON_INSTALL_DIR, 'DLLs', 'tk86t.dll'),
            os.path.join(PYTHON_INSTALL_DIR, 'DLLs', 'tcl86t.dll'),
            os.path.join(PYTHON_INSTALL_DIR, 'Library\\bin', 'sqlite3.dll'),
            os.path.join(PYTHON_INSTALL_DIR, 'Library\\bin', 'mkl_intel_thread.dll')
         ],
    },    
}

setup(
    name = "cameraTest",
    options = options,
    version = "1.0",
    description = '',
    executables = executables
)