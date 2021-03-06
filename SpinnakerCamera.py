## SpinnakerCamera class provides a wrapping for spinnaker API
#
#  SpinnakerCamera controls single spinnaker camera
# TODO: consider switching to storing single JPEG images if performance is insufficient!
import PySpin
#import copy
from collections import deque
import configparser
from acquisition_ini import AcquisitionINI
from data_structures import ImageFormat, StreamProperties, CameraProperties, DisplayProperties, CaptureProperties, TriggerProperties
import datetime
import socket
import shutil
#from SpinnakerControl import SpinnakerControl 


class SpinnakerCamera:
    # Use the following enum and global constant to select the type
    # of AVI video file to be created and saved.       
    class AviType:
        # 'Enum' to select AVI video type to be created and saved
        UNCOMPRESSED = 0 
        MJPG = 1  #!< intraframe-only compression, low processing and memory requirements, compressing ratio~ 1/20
        H264 = 2  #!< interframe compression, high computational load, compressing ratio~ 1/50

    class TriggerType:
        SOFTWARE = 1
        HARDWARE = 2
    
    aviType_ = AviType.MJPG  
    
    def __init__(self, camPtr): 
        #Spinnaker::CameraPtr camPtr
        self.camera_ = camPtr; 
        self.printDeviceInfo()
        self.camera_.Init(); # Initialize camera
        
        self.aviRecorder_ = None #Spinnaker::AVIRecorder 
        self.frameQueue_ = None # circular buffer for frames storing
        self.receivedFramesCnt_ = 0
    
        self.captureOn_ = False  # whether frames are captured into a file
        self.stopCaptureFlag_ = False # flag for stopping the capture
        self.requested_pixelformat = None   #pixel format as configured in the ini file
        self.PySpin_CameraPixelFormat = None      # PySpins enumeration value for the configured pixelformat

        #CAPTURE
        self.PySpin_CapturePixelFormat = None
        self.PySpin_CapturePixelFormatString = None
        #DISPLAY
        self.PySpin_DisplayPixelFormat = None
        self.PySpin_DisplayPixelFormatString = None
        #TRIGGER
        self.PySpin_TriggerMode = None
        self.PySpin_TriggerModeString = None
        
        self.cameraProperties = None
        self.displayProperties = None
        self.captureProperties = None
        self.triggerProperties = None

    def __del__(self):
        self.camera_.DeInit()
        del self.camera_
        print("Spinnaker camera deleted!")
        
        
    ## This function prints the camera information from the transport layer
    # returns: 0 if successful, -1 otherwise. rtype: int
    def printDeviceInfo(self): 
        try:
            result = 0
            nodemap = self.camera_.GetTLDeviceNodeMap()
            nodeDeviceInformation = PySpin.CCategoryPtr(nodemap.GetNode('DeviceInformation'))
            if PySpin.IsAvailable(nodeDeviceInformation) and PySpin.IsReadable(nodeDeviceInformation):
                print('*** DEVICE INFORMATION ***\n')
                features = nodeDeviceInformation.GetFeatures()
                for feature in features:
                    node_feature = PySpin.CValuePtr(feature)
                    print('%s: %s' % (node_feature.GetName(),
                                  node_feature.ToString() if PySpin.IsReadable(node_feature) else 'Node not readable'))
            else:
                print('Device control information not available.')
        except PySpin.SpinnakerException as ex:
            print('Error: %s' % ex)
            result = -1    
        return result

    def getName(self):
       # nodeMapTLDevice = self.camera_.GetTLDeviceNodeMap()
       # ptrDeviceID = nodeMapTLDevice.GetNode('DeviceID')
       # if PySpin.IsAvailable(ptrDeviceID) and PySpin.IsReadable(ptrDeviceID):
       #     name = ptrDeviceID.GetValue()
       #     return name;
        if self.camera_.TLDevice.DeviceID.GetAccessMode() == PySpin.RO:
            name = self.camera_.TLDevice.DeviceID.GetValue()
            # we actually want to usde the serial number as unambiguous identifier here
            serial = self.camera_.TLDevice.DeviceSerialNumber.GetValue()
            return serial;       
        else:
            return None;

    def getSerial(self):
        if self.camera_.TLDevice.DeviceID.GetAccessMode() == PySpin.RO:
            serial = self.camera_.TLDevice.DeviceSerialNumber.GetValue()
            return serial;       
        else:
            return None;

    def getModel(self):        
        if self.camera_.TLDevice.DeviceModelName.GetAccessMode() == PySpin.RO:
            model = self.camera_.TLDevice.DeviceModelName.GetValue()
            return model
        else:
            return None
        
    def setBufferMode(self):
        sNodeMap = self.camera_.GetTLStreamNodeMap() 
        
        # Set  Buffer Handling Mode to OldestFirst
        handlingMode = PySpin.CEnumerationPtr(sNodeMap.GetNode('StreamBufferHandlingMode'))
        if not PySpin.IsAvailable(handlingMode) or not PySpin.IsWritable(handlingMode):
            print('Unable to set Buffer Handling mode (node retrieval). Aborting...\n')
            return False

        handlingModeEntry = PySpin.CEnumEntryPtr(handlingMode.GetCurrentEntry())
        if not PySpin.IsAvailable(handlingModeEntry) or not PySpin.IsReadable(handlingModeEntry):
            print('Unable to set Buffer Handling mode (Entry retrieval). Aborting...\n')
            return False
        
        handlingModeOldestFirst = PySpin.CEnumEntryPtr(handlingMode.GetEntryByName('OldestFirst'))
        if not PySpin.IsAvailable(handlingModeOldestFirst) or not PySpin.IsReadable(handlingModeOldestFirst):
            print('Unable to set Buffer Handling mode (Value retrieval). Aborting...\n')
            return False        

        handlingMode.SetIntValue(handlingModeOldestFirst.GetValue())
        print('Buffer Handling Mode set to OldestFirst...')


        # Set stream buffer Count Mode to manual
        streamBufferCountMode = PySpin.CEnumerationPtr(sNodeMap.GetNode('StreamBufferCountMode'))
        if not PySpin.IsAvailable(streamBufferCountMode) or not PySpin.IsWritable(streamBufferCountMode):
            print('Unable to set Buffer Count Mode (node retrieval). Aborting...\n')
            return False

        streamBufferCountModeManual = PySpin.CEnumEntryPtr(streamBufferCountMode.GetEntryByName('Manual'))
        if not PySpin.IsAvailable(streamBufferCountModeManual) or not PySpin.IsReadable(streamBufferCountModeManual):
            print('Unable to set Buffer Count Mode entry (Entry retrieval). Aborting...\n')
            return False

        streamBufferCountMode.SetIntValue(streamBufferCountModeManual.GetValue())
        print('Stream Buffer Count Mode set to manual...')

        # Retrieve and modify Stream Buffer Count
        bufferCountPtr = PySpin.CIntegerPtr(sNodeMap.GetNode('StreamBufferCountManual'))
        if not PySpin.IsAvailable(bufferCountPtr) or not PySpin.IsWritable(bufferCountPtr):
            print('Unable to set Buffer Count (Integer node retrieval). Aborting...\n')
            return False    
    
        bufferCount = bufferCountPtr.GetMax()           
        NUM_OF_BUFFERS = 50 #
        if (bufferCount > NUM_OF_BUFFERS):
            bufferCount = NUM_OF_BUFFERS
        bufferCountPtr.SetValue(bufferCount)
        #self.camera_.TLStream.StreamDefaultBufferCount.SetValue(bufferCount)
            
        # Display Buffer Info
        print('\nDefault Buffer Handling Mode: %s' % handlingModeEntry.GetDisplayName())
        print('Default Buffer Count: %d' % bufferCountPtr.GetValue())
        print('Maximum Buffer Count: %d' % bufferCountPtr.GetMax())    


    ## Set acquisition mode to continuous
    # output: StreamProperties streamProperties)
    def initStream(self): 
        try:      
            result = 0
            nodemap = self.camera_.GetNodeMap()
            # Enable frame rate control
            # ptrFrameRateControl = PySpin.CCategoryPtr(nodemap.GetNode('AcquisitionFrameRateControlEnable'));
            # if (!Spinnaker::GenApi::IsAvailable(ptrFrameRateControl)) {
            #  print('Unable to retrieve AcquisitionFrameRateControlEnable. Aborting...');
            #  return -1;
            #}
            # ptrFrameRateControl->SetValue("true");
            ptrFrameRate = PySpin.CFloatPtr(nodemap.GetNode('AcquisitionFrameRate'))
            if (not PySpin.IsAvailable(ptrFrameRate)) or (not PySpin.IsReadable(ptrFrameRate)):
                print('Unable to retrieve frame rate. Aborting...')
                return -1, None
    
            streamProperties = StreamProperties(self.camera_.Width.GetValue(), self.camera_.Height.GetValue(), ptrFrameRate.GetValue())
    
            #get Camera Model to choose pixel format
            deviceModel = self.getModel()
            if deviceModel == None:
                return -1, None
            print('%s' % deviceModel)
            #cameraType = deviceModel[-1]
                  
            nodePixelFormat = PySpin.CEnumerationPtr(nodemap.GetNode('PixelFormat'))

            if PySpin.IsAvailable(nodePixelFormat) and PySpin.IsWritable(nodePixelFormat):
                # the goal is simply to extract the current camera's/display's/capture's configured pixelformat from acquisition.ini
                self.cameraProperties, self.displayProperties, self.captureProperties, self.triggerProperties = self.getSubsectionsFromIniFileForCurrentCamera()
 
                #this is now generic for all pixelformats
                nodePixelFormatValue = PySpin.CEnumEntryPtr(nodePixelFormat.GetEntryByName(self.cameraProperties.pixelFormat))              
                #print('nodePixelFormatValue: %s' % nodePixelFormatValue)
                #print('PySpin.PixelFormat_Mono8: %s' % PySpin.PixelFormat_Mono8)
                
                #DISPLAY
                self.PySpin_DisplayPixelFormatString = self.displayProperties.pixelFormat                
                self.PySpin_DisplayPixelFormat, streamProperties_format = self.getPySpinPixelTypeEnumValueFromString(self.displayProperties.pixelFormat)
                #print('PySpin_DisplayPixelFormat: %s' % str(self.PySpin_DisplayPixelFormat))
                if self.displayProperties.pixelFormat != self.cameraProperties.pixelFormat:
                    print('Camera and display pixelformat differ, requiring costly conversion, consider setting display pixelformat to camera pixelformat if possible.')
                    print('self.cameraProperties.pixelFormat: %s' % self.cameraProperties.pixelFormat)
                    print('self.displayProperties.pixelFormat: %s' % self.displayProperties.pixelFormat)

                if (self.displayProperties.pixelFormat == 'RGB8') or (self.displayProperties.pixelFormat == 'Mono8'):
                    print('Requested display pixelformat supported: %s' % self.displayProperties.pixelFormat)
                else:
                    print('display pixel format %s' % self.displayProperties.pixelFormat, 'not supported (only RGB8 and Mono8) Aborting...')
                    return -1, None
                    
                #CAPTURE
                self.PySpin_CapturePixelFormatString = self.captureProperties.pixelFormat
                self.PySpin_CapturePixelFormat, streamProperties_format = self.getPySpinPixelTypeEnumValueFromString(self.captureProperties.pixelFormat)
                #print('PySpin_CapturePixelFormat: %s' % self.PySpin_CapturePixelFormat)
                
                if self.captureProperties.pixelFormat != self.cameraProperties.pixelFormat:
                    print('Camera and capture pixelformat differ, requiring costly conversion, consider setting capture pixelformat to camera pixelformat if possible.')
                    print('self.cameraProperties.pixelFormat: %s' % self.cameraProperties.pixelFormat)
                    print('self.captureProperties.pixelFormat: %s' % self.captureProperties.pixelFormat)


                # Retrieve the desired entry node from the enumeration node
                if PySpin.IsAvailable(nodePixelFormatValue) and PySpin.IsReadable(nodePixelFormatValue):
                    # Retrieve the integer value from the entry node
                    pixelFormat = nodePixelFormatValue.GetValue()
                    # Set integer as new value for enumeration node
                    nodePixelFormat.SetIntValue(pixelFormat)
                    print('Pixel format set to %s...' % nodePixelFormat.GetCurrentEntry().GetSymbolic())
                else:
                    print('Pixel format not available...')
                    result = -1
                    # try to be helpful
                    tmp_nodePixelFormat = PySpin.CEnumerationPtr(nodemap.GetNode('PixelFormat'))
                    node_list = tmp_nodePixelFormat.GetEntries()
                    supported_pixelformat_string = ''
                    print('PixelFormats supported by this camera:')
                    for i_node in node_list:
                        node_enum = PySpin.CEnumEntryPtr(i_node)
                        if not PySpin.IsAvailable(node_enum) or not PySpin.IsReadable(node_enum):
                            continue
                        supported_pixelformat_string += '{} '.format(node_enum.GetSymbolic())
                
                    print('%s' % supported_pixelformat_string)   


                self.PySpin_CameraPixelFormat, streamProperties.format = self.getPySpinPixelTypeEnumValueFromString(self.cameraProperties.pixelFormat)
#                print('PySpin_CameraPixelFormat: %s' % self.PySpin_CameraPixelFormat)
                    
                if self.PySpin_DisplayPixelFormatString != self.cameraProperties.pixelFormat:
                    print('Display pixelformat differs from camera pixelformat, requiring costly conversions.')
                    
            self.setBufferMode()                
            self.enableFrameRateSetting()

        except PySpin.SpinnakerException as ex:
            print('Error: %s for the camera %s' % (ex, self.getName()) )
            return -1, None
        return result, streamProperties


    ## Set acquisition mode to continuous
    def start(self, bufferCapacity):       
        try:
            nodemap = self.camera_.GetNodeMap()
            ptrAcquisitionMode = PySpin.CEnumerationPtr(nodemap.GetNode('AcquisitionMode'))
            if not PySpin.IsAvailable(ptrAcquisitionMode) or not PySpin.IsWritable(ptrAcquisitionMode):
                print('Unable to set acquisition mode to continuous (node retrieval). Aborting... \n')
                return -1

            ptrAcquisitionModeContinuous = ptrAcquisitionMode.GetEntryByName('Continuous')
            if not PySpin.IsAvailable(ptrAcquisitionModeContinuous) or not PySpin.IsReadable(ptrAcquisitionModeContinuous):
                print('Unable to set acquisition mode to continuous (entry \'continuous\' retrieval). \Aborting... \n')
                return -1
            
            acquisitionModeContinuous = ptrAcquisitionModeContinuous.GetValue();
            ptrAcquisitionMode.SetIntValue(acquisitionModeContinuous);
            print('Acquisition mode set to continuous...');
            
            if (self.frameQueue_ != None):
                del self.frameQueue_;
            self.frameQueue_ = deque(maxlen = 1000)
            self.camera_.BeginAcquisition()# Begin acquiring images

        except PySpin.SpinnakerException as ex:
            print('Error: %s for the camera %s' % (ex, self.getName()) )
            return -1
        return 0


    
    def acquireFrames(self, needGetImage):
        #!! TODO: acquire all frames in the buffer
        result = -1
        frameBuf = None
        try:  
            frame = self.camera_.GetNextImage(2);            
            # Ensure image completion
            if frame.IsIncomplete():
                print('Image incomplete with image status %d ... \n' % frame.GetImageStatus())
            else:
                i = 0
                while (not frame.IsIncomplete()):
                    if needGetImage: # if we need to copy image to frameBuf
                        frameBuf = frame.GetData()  
                    result = 0                          
                    if self.captureOn_:
                        #std::cout << receivedFramesCnt_ <<"\n";
                        self.receivedFramesCnt_ += 1
                        #frameQueue_.push(frame); # Deep copy image into image vector
                        #frameQueue_.push_back(frame);
                        
                        # self.PySpin_CameraPixelFormat is configured in init stream above  
                        # this should affect writing to file only...
                        if self.requested_pixelformat == self.PySpin_CapturePixelFormatString:
                            self.frameQueue_.append(frame.Convert(self.PySpin_CapturePixelFormat, PySpin.NO_COLOR_PROCESSING))
                            #print('PySpin.NO_COLOR_PROCESSING: %s' % PySpin.NO_COLOR_PROCESSING)
                        else:
                            self.frameQueue_.append(frame.Convert(self.PySpin_CapturePixelFormat, PySpin.HQ_LINEAR))
                            #print('PySpin.HQ_LINEAR: %s' % PySpin.HQ_LINEAR)
                    
                    # convert image for display purposes?
                    #print('self.PySpin_DisplayPixelFormatString: %s' % self.PySpin_DisplayPixelFormatString)
                    #print('self.cameraProperties.pixelFormat: %s' % self.cameraProperties.pixelFormat)
                    if self.displayProperties.pixelFormat != self.cameraProperties.pixelFormat:
                        #print('Displaying as different format from capture')
                        tmpframeBuf = frame.Convert(self.PySpin_DisplayPixelFormat, PySpin.HQ_LINEAR)
                        frameBuf = tmpframeBuf.GetData()
                          
                    frame.Release();
                    i += 1;
                    #if (i >= 2)
                    #  break;
                    frame = self.camera_.GetNextImage(PySpin.EVENT_TIMEOUT_NONE);

                frame.Release();

        except PySpin.SpinnakerException as ex:
            if ex.errorcode != PySpin.SPINNAKER_ERR_TIMEOUT:
                print('Error: %s' % ex)
                result = -1
                
        return result, frameBuf
         
        
    def processFrame(self):
        result = -1
        if len(self.frameQueue_) < 1: #!< if the buffer is empty - exit, since there is nothing to do
            return 0, None;
        try:  
            if (self.captureOn_ or self.stopCaptureFlag_):
                 frameBuf = self.frameQueue_.popleft();
                 self.aviRecorder_.Append(frameBuf);
                 print('Received: %s, In buffer: %s\n' %(self.receivedFramesCnt_, len(self.frameQueue_)))
                 if self.stopCaptureFlag_:
                     if self.captureOn_:
                         self.captureOn_ = False; 
                         #!< capture is finished. From now on we just write to file 
                         #!< remaining frames from the buffer
                                                     

                     if len(self.frameQueue_) == 0:  #!< if the buffer is empty
                         self.aviRecorder_.Close();      #!< close the file and
                         print('Video saved!\n');
                         self.stopCaptureFlag_ = False;     #!< clear the flag
            result = 0; #!< finish successfully                                     
    
        except PySpin.SpinnakerException as ex:
            print('Frame Processing Error: %s' % ex)
            return -1, None
        return result     

#  int j = frameQueue_.size();
#  for (;j > 0; --j) {
#    aviRecorder_.AVIAppend(frameQueue_.front());
#    frameQueue_.pop_front();

       
    ## Ends acquisition: ensure that devices clean up properly
    def stop(self):
        try:
            self.camera_.EndAcquisition();          
        except PySpin.SpinnakerException as ex:
            print('Error: %s for the camera %s' % ex, self.camera_ )


    #! TODO: the generated name is not unique but has a constant postfix 0000: correct this!
    def startCapture(self):
        result = 0;
        self.stopCaptureFlag_ = False
        print('*** CREATING VIDEO ***\n')

        try:      
            # Retrieve device serial number for filename
            deviceSerialNumber = ''
            nodeMapTLDevice = self.camera_.GetTLDeviceNodeMap()
            nodeSerial = PySpin.CStringPtr(nodeMapTLDevice.GetNode('DeviceSerialNumber'))
            if PySpin.IsAvailable(nodeSerial) and PySpin.IsReadable(nodeSerial):
                deviceSerialNumber = nodeSerial.GetValue()
                print('Device serial number retrieved as %s...' % deviceSerialNumber)

            #! Set frame rate equal to the current acquisition frame rate (Hz)
            nodemap = self.camera_.GetNodeMap()       
            nodeFramerate = PySpin.CFloatPtr(nodemap.GetNode('AcquisitionFrameRate'))
            if (not PySpin.IsAvailable(nodeFramerate)) or (not PySpin.IsReadable(nodeFramerate)):
                print('Unable to retrieve frame rate. Aborting...')
                return -1
            frameRateToSet = nodeFramerate.GetValue();
            print('Frame rate to be set to %d...' % frameRateToSet)
       
            #! Create a unique filename and configure file parameters
            self.aviRecorder_ = PySpin.SpinVideo()
            
            aviFilename = '%s%sSN%s.%s.%s' % (self.captureProperties.outputPath, self.captureProperties.cameraPrefix , deviceSerialNumber, datetime.datetime.now().strftime("%Y%m%dT%H%M%S"), self.captureProperties.cameraSuffix)
            
            # use the configured options
            if self.captureProperties.aviType == 'UNCOMPRESSED':
                self.aviType_ = self.AviType.UNCOMPRESSED
            elif self.captureProperties.aviType == 'MJPG':
                self.aviType_ = self.AviType.MJPG
            elif self.captureProperties.aviType == 'H264':
                self.aviType_ = self.AviType.H264
            else:
                print('Unknown aviType (', self.captureProperties.aviType, ') requested, only UNCOMPRESSED, MJPG and H264 supported')
        


            if self.aviType_ == self.AviType.UNCOMPRESSED:
                #aviFilename = 'SaveToAvi-Uncompressed-%s' % deviceSerialNumber
                option = PySpin.AVIOption()
                    
            elif self.aviType_ == self.AviType.MJPG:
                #aviFilename = 'SaveToAvi-MJPG-%s' % (deviceSerialNumber,)   
                option = PySpin.MJPGOption()
                #option.quality = 75
                option.quality = self.captureProperties.MJPGQuality
    
            elif self.aviType_ == self.AviType.H264:
                #aviFilename = 'SaveToAvi-H264-%s' % deviceSerialNumber    
                option = PySpin.H264Option()
                #option.bitrate = 1000000
                option.bitrate = self.captureProperties.H264BitRate
                option.height = self.camera_.Height.GetValue()
                option.width = self.camera_.Width.GetValue()
    
            else:
                print('Error: Unknown AviType. Aborting...')
                return -1
            option.frameRate = frameRateToSet
            self.aviRecorder_.Open(aviFilename, option)
            #! note that AVIRecorder takes care of the file extension
            print("Video is saving at %s.avi\n" % aviFilename)
            
            sNodeMap = self.camera_.GetTLStreamNodeMap() 
            streamNode = PySpin.CIntegerPtr(sNodeMap.GetNode('StreamTotalBufferCount'))
            if not PySpin.IsAvailable(streamNode) or not PySpin.IsReadable(streamNode):
                print('Unable to get Stream Total Buffer Count (node retrieval). Aborting...\n')
                return False
            #Spinnaker::GenApi::INodeMap& sNodeMap = camera_->GetTLStreamNodeMap();
            #Spinnaker::GenApi::CIntegerPtr streamNode = sNodeMap.GetNode("StreamTotalBufferCount");
            self.receivedFramesCnt_ = streamNode.GetValue();
            
            self.captureOn_ = True
            self.processFrame()
        except PySpin.SpinnakerException as ex:
            print('Error: %s' % ex)
            return -1
        return result             
        
 
    ## Stops capturing new frames.
    # AVI file will be closed only after buffer is purged!
    def stopCapture(self):
        self.stopCaptureFlag_ = True
             

    def enableTrigger(self, triggerTypeToSet):
        # Ensure trigger mode off
        # The trigger must be disabled in order to configure whether the source
        # is software or hardware.
        result = self.disableTrigger()
        if result != 0:
            return result
        if self.camera_.TriggerSource.GetAccessMode() != PySpin.RW:
            print('Unable to get trigger source (node retrieval). Aborting...')
            return -1
        if triggerTypeToSet == self.TriggerType.SOFTWARE:
            self.camera_.TriggerSource.SetValue(PySpin.TriggerSource_Software)
        elif triggerTypeToSet == self.TriggerType.HARDWARE:
            self.camera_.TriggerSource.SetValue(PySpin.TriggerSource_Line0)
        return 0
        

    def disableTrigger(self):
        if self.camera_.TriggerMode.GetAccessMode() != PySpin.RW:
            print('Unable to disable trigger mode (node retrieval). Aborting...')
            return -1
        self.camera_.TriggerMode.SetValue(PySpin.TriggerMode_Off)
        print('Trigger mode disabled...')
        return 0


    def enableFrameRateSetting(self):
         nodeMap = self.camera_.GetNodeMap();
         acqFrameRate =  PySpin.CEnumerationPtr(nodeMap.GetNode("AcquisitionFrameRateAuto"));
         if (not PySpin.IsAvailable(acqFrameRate)) or (not PySpin.IsWritable(acqFrameRate)): 
             print('Unable to retrieve AcquisitionFrameRateAuto. Aborting...')
             return -1
         acqFrameRateAutoOff = PySpin.CEnumEntryPtr(acqFrameRate.GetEntryByName('Off'))
         if not PySpin.IsAvailable(acqFrameRateAutoOff) or not PySpin.IsReadable(acqFrameRateAutoOff):
             print('Unable to set Buffer Handling mode (Value retrieval). Aborting...\n')
             return -1
         # setting up a value for the FrameRate auto ( 0 = Off, 1 = Once, 2= Continous )
         acqFrameRate.SetIntValue(acqFrameRateAutoOff.GetValue()) # setting to Off

         frameRateEnable = PySpin.CBooleanPtr(nodeMap.GetNode("AcquisitionFrameRateEnabled"));
         if (not PySpin.IsAvailable(acqFrameRate)) or (not PySpin.IsWritable(acqFrameRate)): 
             print('Unable to retrieve AcqFrameRateEnable. Aborting...')
             return -1
         frameRateEnable.SetValue(True)
         return 0;
    
    
    def setFrameRate(self, frameRate):
        nodemap = self.camera_.GetNodeMap()
        nodeAcquisitionFramerate = PySpin.CFloatPtr(nodemap.GetNode("AcquisitionFrameRate"))
        if not PySpin.IsAvailable(nodeAcquisitionFramerate) and not PySpin.IsReadable(nodeAcquisitionFramerate):
            print('Unable to retrieve frame rate. Aborting...')
            return -1
        nodeAcquisitionFramerate.SetValue(frameRate)
        print('Frame rate set to %d...' % frameRate)      
        return 0
        
    def getFrameRate(self):
        nodemap = self.camera_.GetNodeMap()
        nodeAcquisitionFramerate = PySpin.CFloatPtr(nodemap.GetNode("AcquisitionFrameRate"))
        if not PySpin.IsAvailable(nodeAcquisitionFramerate) and not PySpin.IsReadable(nodeAcquisitionFramerate):
            print('Unable to retrieve frame rate. Aborting...')
            return -1
        frameRate = nodeAcquisitionFramerate.GetValue()
        return frameRate


    def enableExposureAuto(self):
        if self.camera_.ExposureAuto.GetAccessMode() != PySpin.RW:
            print('Unable to enable automatic exposure. Aborting...')
            return -1
        self.camera_.ExposureAuto.SetValue(PySpin.ExposureAuto_On)
        print('Automatic exposure enabled...')
        return 0
    
    
    def disableExposureAuto(self):
        if self.camera_.ExposureAuto.GetAccessMode() != PySpin.RW:
            print('Unable to disable automatic exposure. Aborting...')
            return -1
        self.camera_.ExposureAuto.SetValue(PySpin.ExposureAuto_Off)
        print('Automatic exposure disabled...')
        return 0
    
    # exposure time in microseconds
    def setExposureTime(self, exposureTime):
        self.disableExposureAuto();        
        if self.camera_.ExposureTime.GetAccessMode() != PySpin.RW:
            print('Unable to set exposure time. Aborting...')
            return -1
        # Ensure desired exposure time does not exceed the maximum
        exposureTime = min(self.camera_.ExposureTime.GetMax(), exposureTime)
        self.camera_.ExposureTime.SetValue(exposureTime)
        return 0
    
        
    def getExposureTime(self):
        if self.camera_.ExposureTime.GetAccessMode() != PySpin.RW:
            print('Unable to get exposure time. Aborting...')
            return -1
        # Ensure desired exposure time does not exceed the maximum
        exposureTime = self.camera_.ExposureTime.GetValue()
        return exposureTime
    

    def enableGainAuto(self):
        if self.camera_.ExposureAuto.GetAccessMode() != PySpin.RW:
            print('Unable to enable automatic exposure. Aborting...')
            return -1
        self.camera_.GainAuto.SetValue(PySpin.GainAuto_On)
        print('Automatic gain enabled...')
        return 0
    
    
    def disableGainAuto(self):
        if self.camera_.ExposureAuto.GetAccessMode() != PySpin.RW:
            print('Unable to disable automatic gain. Aborting...')
            return -1
        self.camera_.GainAuto.SetValue(PySpin.GainAuto_Off)
        print('Automatic gain disabled...')
        return 0
    
    
    def setGain(self, gain):
        self.disableGainAuto();        
        if self.camera_.Gain.GetAccessMode() != PySpin.RW:
            print('Unable to set gain. Aborting...')
            return -1
        # Ensure desired exposure time does not exceed the maximum
        #gain = min(self.camera_.Gain.GetMax(), gain)
        self.camera_.Gain.SetValue(gain)
        return 0
            
    def getGain(self):
        if self.camera_.ExposureTime.GetAccessMode() != PySpin.RW:
            print('Unable to get gain. Aborting...')
            return -1
        # Ensure desired exposure time does not exceed the maximum
        exposureTime = self.camera_.Gain.GetValue()
        return exposureTime
    
   
    
    def setHorizontalFlip(self, value): # bool
        if self.camera_.ExposureTime.GetAccessMode() != PySpin.RW:
            print('Unable to set horizontal flip. Aborting...')
            return -1
        #print ('value: %s' % value)
        self.camera_.ReverseX.SetValue((value == 'True'), True)
        #print('self.camera_.ReverseX.SetValue() %s' % value)
        return 0
    
    def getHorizontalFlip(self):
        if self.camera_.ExposureTime.GetAccessMode() != PySpin.RW:
            print('Unable to get vertical flip. Aborting...')
            return -1
        isFlip = self.camera_.ReverseX.GetValue()
        #print('self.camera_.ReverseX.GetValue() %s' % isFlip)
        return isFlip        
 
    
    def setVerticalFlip(self, value): # bool
        if self.camera_.ExposureTime.GetAccessMode() != PySpin.RW:
            print('Unable to set vertical flip. Aborting...')
            return -1
        print('value: %s' % value)
        self.camera_.ReverseY.SetValue((value == 'True'), True)
        print('self.camera_.ReverseY.SetValue() %s' % value)
        return 0
    
    def getVerticalFlip(self):
        if self.camera_.ExposureTime.GetAccessMode() != PySpin.RW:
            print('Unable to get vertical flip. Aborting...')
            return -1
        isFlip = self.camera_.ReverseY.GetValue()
        #print('self.camera_.ReverseY.GetValue() %s' % isFlip)
        return isFlip


    def getPySpinPixelTypeEnumValueFromString(self, PixelFormatString):
        PySpinPixelTypeEnumValue = -1 # Mono8 equals 1    
        streamProperties_format = 'None'

        current_PySpinPixelFormatEnumName = 'PixelFormat_' + PixelFormatString
        PySpinPixelTypeEnumValue = getattr(PySpin, current_PySpinPixelFormatEnumName)
        #print('DEBUG: getattr(PySpin, %s: %s' % (current_PySpinPixelFormatEnumName, PySpinPixelTypeEnumValue))
        
        # use this to configure all relavant variables per pixelformat, ideally this gets removed completely
        if PixelFormatString == 'RGB8':
            streamProperties_format = ImageFormat.RGB24
        elif PixelFormatString == 'Mono8':
            streamProperties_format = ImageFormat.MONO8
        elif PixelFormatString == 'Mono12Packed':
            streamProperties_format = ImageFormat.RGB24
        elif PixelFormatString == 'Mono12p':
            streamProperties_format = ImageFormat.RGB24
        elif PixelFormatString == 'Mono16':
            streamProperties_format = ImageFormat.Mono16
        elif PixelFormatString == 'BayerGR8':
            streamProperties_format = ImageFormat.RGB24
        elif PixelFormatString == 'BayerGR12p':
            streamProperties_format = ImageFormat.RGB24
        elif PixelFormatString == 'BayerGR12Packed':
            streamProperties_format = ImageFormat.RGB24
        elif PixelFormatString == 'BayerGR16':
            streamProperties_format = ImageFormat.RGB24
        elif PixelFormatString == 'YCbCr411_8_CbYYCrYY':
            streamProperties_format = ImageFormat.RGB24
        elif PixelFormatString == 'YCbCr422_8_CbYCrY':
            streamProperties_format = ImageFormat.RGB24
            #PySpinPixelTypeEnumValue = PySpin.PixelFormat_YCbCr422_8_CbYCrY
        elif PixelFormatString == 'YCbCr8_CbYCr':
            streamProperties_format = ImageFormat.RGB24
        else:
           print('The following pixelformat is not yet handled: %s' % PixelFormatString)   

#        print('getPySpinPixelTypeEnumValueFromString: PixelFormatString: %s' % PixelFormatString)
#        print('getPySpinPixelTypeEnumValueFromString: PySpinPixelTypeEnumValue: %s' % PySpinPixelTypeEnumValue)
   
        return PySpinPixelTypeEnumValue, streamProperties_format


    def getSubsectionsFromIniFileForCurrentCamera(self):
        cameraName = self.getName()
#        cameraSerialNum = self.getSerial()
#        print('cameraSerialNum: %s' % cameraSerialNum)
        
        # This should be folded back into acquisition_ini to avaoid configuring the ini file name in two positions....
        self.iniFile_ = AcquisitionINI()
        ini_file_name = "acquisition.ini"
#        cameraProperties = self.iniFile_.getCameraProperties(cameraName)
#        displayProperties = self.iniFile_.getDisplayProperties(cameraName)
#        captureProperties = self.iniFile_.getCaptureProperties(cameraName)
#        triggerProperties = self.iniFile_.getTriggerProperties(cameraName)


        cameraModel = self.getModel()
        # re-create the key
        sectionFullName = cameraModel + ", ID " + cameraName# + ", Camera"
        print('acquisition.ini sectionFullName: %s' % sectionFullName)
        
        # the ini file was already checked, so we simply assume a clean ini file
        self.config_ = configparser.RawConfigParser()
        self.config_.optionxform = lambda option: option # switch to case-preserving mode 
        self.config_.read(ini_file_name)
        if self.config_.has_section(sectionFullName + ", Camera"):
            labels, entries = zip(*self.config_.items(sectionFullName + ", Camera"))
            cameraProperties = CameraProperties(*entries)
        else:
            print('Could not read sectionFullName: %s' % sectionFullName + ", Camera")
            #self.iniFile_.checkAndRecreateSection(self.iniFile_.defaultSectionTitle_, self.iniFile_.cameraSubsectionTitle_)
            cameraProperties = self.iniFile_.getCameraProperties(cameraName)
                
        

        if self.config_.has_section(sectionFullName + ", Display"):
            labels, entries = zip(*self.config_.items(sectionFullName + ", Display"))
            displayProperties = DisplayProperties(*entries)
        else:
            print('Could not read sectionFullName: %s' % sectionFullName + ", Display")                
            displayProperties = self.iniFile_.getDisplayProperties(cameraName)

        if self.config_.has_section(sectionFullName + ", Capture"):
            labels, entries = zip(*self.config_.items(sectionFullName + ", Capture"))
            captureProperties = CaptureProperties(*entries)
        else:
            print('Could not read sectionFullName: %s' % sectionFullName + ", Capture")                
            captureProperties = self.iniFile_.getCaptureProperties(cameraName)

        if self.config_.has_section(sectionFullName + ", Trigger"):
            labels, entries = zip(*self.config_.items(sectionFullName + ", Trigger"))
            triggerProperties = TriggerProperties(*entries)
        else:
            print('Could not read sectionFullName: %s' % sectionFullName + ", Trigger")                
            triggerProperties = self.iniFile_.getTriggerProperties(cameraName)


        #print('self.cameraProperties.pixelFormat: %s' % cameraProperties.pixelFormat)
        del self.config_
        
        #save the ini file to where the video files are written
        host_name = socket.getfqdn()
        output_aquisition_ini_fqn = '%s%s.%s' % (captureProperties.outputPath, ini_file_name, host_name)
        shutil.copy2(ini_file_name, output_aquisition_ini_fqn)
        
        
        return cameraProperties, displayProperties, captureProperties, triggerProperties