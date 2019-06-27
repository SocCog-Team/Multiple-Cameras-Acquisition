import ctypes
import PySpin
from VideoSingleton import VideoSingleton
from data_structures import CameraProperties

# class for checking available memory
class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("sullAvailExtendedVirtual", ctypes.c_ulonglong)
    ]

    def __init__(self):
        # have to initialize this to the size of MEMORYSTATUSEX
        self.dwLength = ctypes.sizeof(self)
        super(MEMORYSTATUSEX, self).__init__()
        

class SpinnakerControl:       
    def __init__(self): 
        self.acquisitionOn_ = False  # whether acquisition is on
        self.recordingOn_ = False  # whether recording is on

        self.videoSources_ = [] # list of objects controlling cameras and stream from them
        self.names_ = []   # list of cameras' names
        self.camList_ = None # list of cameras references, data from it are used by videoSources_
        
        # Retrieve reference to system object essential for Spinnaker Api
        self.system_ = PySpin.System.GetInstance()

        # Get current library version
        version = self.system_.GetLibraryVersion()
        print('Library version: %d.%d.%d.%d' % (version.major, version.minor, version.type, version.build))


    def __del__(self):
        # Release instance
        if self.camList_ != None:
            self.camList_.Clear()
        self.system_.ReleaseInstance()
        print("SpinnakerControl deleted!")

    ## auxilary function returning available memory used in startAcquisition
    # ouput long long int
    def getAvailableSystemMemory(self):
        status = MEMORYSTATUSEX()
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)) 
        
        # return status.ullAvailVirtual;
        return status.ullAvailPhys;


    ## initializes list of cameras; creates objects VideoSingleton for each of them;
    #  gets their names and stores them in a list
    #  output: error code (if < 0) or number of camera (if > 0)
    def initCameras(self):    
        result = 0
            
        # Retrieve list of cameras from the system
        try:
            if len(self.videoSources_) > 0:
                self.close();
            self.camList_ = self.system_.GetCameras()
            numCameras = self.camList_.GetSize()
            print('Number of cameras detected:', numCameras)     
                    
            for i in range (0, numCameras):
                self.videoSources_.append(VideoSingleton(i, self.camList_.GetByIndex(i)))
                res, cameraName = self.videoSources_[i].open()
                self.names_.append(cameraName)
                result += res
            if result == 0:
                result = numCameras
        except PySpin.SpinnakerException as ex:
            print('Error: %s' % ex)
            result = -1    
        return result
  
       

    ## for every camera computes the capacity of buffer for the streams 
    #  and launches the acquisition
    def startAcquisition(self): 
          nVideoSource = len(self.videoSources_);
          if nVideoSource <= 0:
            return -1;
        
          # compute total available memory
          totalMemory = self.getAvailableSystemMemory();
        
          # compute the share of memory to be assigned for buffers of every stream
          # for every frame i: weight[i] = frameSize*frameRate[i]^2
          # (we take square of frame rate to provide more space for streams with higher load)
          totalWeight = 0.0;
          frameSize = []
          weightOfStream = []
          for i in range(0, nVideoSource):
              streamProperties = self.videoSources_[i].streamProperties_
              frameSize.append(streamProperties.getFrameSize());
              weightOfStream.append(frameSize[i]*(streamProperties.fps**2));
              totalWeight += weightOfStream[i];
        
          # memoryShare[i] = weight[i]/sum_of_weights
          # buffer capacity = memoryShare[i]*totalMemory/frameSize[i]
          # since buffer capacity is in frames, not in bytes
          for i in range(0, nVideoSource):
              memoryShare = weightOfStream[i]/totalWeight;
              assignedBufferCapacity = totalMemory*memoryShare/frameSize[i];
              self.videoSources_[i].startAcquisition(assignedBufferCapacity);
        
          self.AcquisitionOn_ = True;
          return 0


    ## launches recording for all cameras
    def startRecording(self):   
        for x in self.videoSources_:
            x.startRecording()
        self.recordingOn_ = True
        
        
    ## stops recording for all cameras
    def stopRecording(self):
        for x in self.videoSources_:
            x.stopRecording()
        self.recordingOn_ = False        
  

    # stops acquisition for all cameras
    def stopAcquisition(self): 
        for x in self.videoSources_:
            x.stopAcquisition()
        self.acquisitionOn_ = False

                        
    ## stops recording and acquisition, clears all data structures    
    def close(self): 
        if self.recordingOn_:
            self.stopRecording()
        if self.acquisitionOn_:
            self.stopAcquisition()

        del self.videoSources_[:]
        del self.names_[:]
        self.camList_.Clear(); # Clear camera list before releasing system


    ## int index, CameraProperties &properties:
    def setParameters(self, index, cameraProperties, displayProperties):
        result = -1
        if (index < len(self.videoSources_) and (index >= 0)):
            print(cameraProperties.fps)
            result = self.videoSources_[index].setParameters(cameraProperties, displayProperties)
        return result