# Multiple-Cameras-Acquisition
code for acquiring video from several FLIR Chamelion 3 cameras

# To do:

- synchonisation of acquisition from several cameras using sowtware/hardware trigger;

- implementation of acquisition/recording control through a network (allowing camera control through EventIDE and synchonisation of video acquisition by the software on several machines)

- adapting the code to the needs of specific setups

- change the interpretation of -1 to mean Auto for gain and exposure time, add a toggle for the white balance add a per camera save path and file prefix/suffix

- add pixelformat as a configurable to the ini file (also abstract the additional pixelformat dependent parameters like size of the backing buffer and the pixelformat enumeration values).

# Code structure:

1. Principal classes

1.1 SpinnakerControl controls the camera system and is responsible for the most general actions (start/stop recording by all cameras, start/stop acquisition by all cameras, etc)

1.2 VideoSingleton is a COMPOSITION of classes providing a full control of a single video stream (start/stop recording by specific camera, start/stop acquisition by specific camera, etc). It is composed out of the following classes:

- SpinnakerCamera (responsible for acquisition) providing access to basic camera functions based on Spinnaker SDK

- VideoAcquisitionThread acquiring frames from the camera. It puts each frame to a queue for saving to a video file and to a buffer for displaying.

- VideoProcessingThread saving frames from a queue to a video file.

- wxWindow (responsible for video display) defining window and graphical elements for the output of the acquired video

2 Principal auxillary classes

2.1 SpinnakerCamera provides an interface for a single camera control. This class isa wrapping spinnaker API

2.2 VideoAcquisitionThread acquiring frames from the camera. It puts each frame to a queue for saving to a video file and to a buffer for displaying. Each SpinnakerCamera instance should have own instance of VideoAcquisitionThread

2.3 VideoProcessingThread saving frames from a queue to a video file. Each SpinnakerCamera instance should have own instance of VideoProcessingThread

3. Other auxillary classes and units

3.1 main_control_window defines MainWindow (inherited from wx.Frame) and inherites 
from it VideoAcquisitionControl, a window for controlling acquisition and recording. 

3.2 wxWindow defines window and graphical elements for the output of the acquired video using wxPython toolkit and PIL image class (for the color format transformation).

- class VideoDisplay defines a window for displaying the acquired frames:

- class VideoPanel defines a graphical panel for displaying the acquired frames

3.3 data_structures defines several data structures used throughout the project: 

- ImageFormat: constants specifying pixel format in acquired and displayed frames
    
- StreamProperties: properties of the frames stream sent by a camera (dimensions, frame rate, pixel format)
    
- CameraProperties: various camera settings including frame rate, exposure time, gain, etc. 
        
- DisplayProperties: display settings (window size, whether stretching is allowed, etc)

3.4 acquisition_ini unit defines AcquisitionINI class for reading/writing cameras and display settings to ini file

4. setup.py - script for creating an executable version

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

# Notes:

The SDK version 1.23.0.27 can not store video in RGB8 format (YCBCr8_CbYCr should work, but will produce wrong colors for the display, as for perfomance sake this application does not do color conversions)
