# Multiple-Cameras-Acquisition
code for acquiring video from several FLIR Chamelion 3 cameras


# Installation guide:
1.	Get latest anaconda for windows: https://www.anaconda.com/download/

2.	Create python 3.6 environment. Command prompt: 

- conda create -n py36 python=3.6 anaconda
  
- activate py36

3.	Installing PySpin. Command prompt:

- pip install PyQt5==5.9.2 
  
- python -m ensurepip
  
- python -m pip install --upgrade pip numpy matplotlib
  
- python -m pip install spinnaker-python-1.19.0.22-cp36-cp36m-win_amd64.whl
  

4.	Other important components. Command prompt:

- pip install wxPython
  
- pip install pillow

5.	Change Environmental Variables by adding “\envs\py36” to all anaconda related path variables

6.	To be able to create exe-files:

6.1 Command prompt:
  
- conda install mkl=2018.0.2

- pip install cx_Freeze

- pip install idna

6.2	open command prompt at source files location:

- activate py36
  
-  python setup.py build
