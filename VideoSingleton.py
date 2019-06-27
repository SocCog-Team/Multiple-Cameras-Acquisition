# -*- coding: utf-8 -*-
"""
Created on Thu Jan  3 13:38:55 2019

VideoSingleton class is a COMPOSITION of classes providing a full control 
of a single video stream (start/stop recording by specific camera, 
start/stop acquisition by specific camera, etc). 

@author: taskcontroller
"""

#  This class contains two threads: first acquires frames and put them into a buffer,
#  second processes frames and saves them to avi file or to bmp files.
#  VideoSingleton also owns the window where the acquired video is displayed.

from VideoProcessingThread import VideoProcessingThread
from VideoAcquisitionThread import VideoAcquisitionThread
from data_structures import CameraProperties
from SpinnakerCamera import SpinnakerCamera
from wxWindow import VideoDisplay


class VideoSingleton:
    INITIAL_WINDOW_WIDTH = 320;
    INITIAL_WINDOW_HEIGHT = 256;
    DISPLAY_FRAME_RATE = 25;

    #constructor; input: camera index and pointer to the camera
    def __init__(self, camIndex = 0, camPtr = None): 
        # index of the camera in camera list; 
        # currently used only for correct initial location of the output window
        self.cameraIndex_ = camIndex
        
        # object for the control of the camera using Spinnaker API
        self.spinnakerCamera_ = SpinnakerCamera(camPtr); 
        self.acquisitionOn_ = False # whether acquisition is on
        
        self.videoDisplay_ = VideoDisplay()  # window to display the acquired video frames
        self.streamProperties_ = None # structure containing frame information

        # thread that acquires frames and put them into a buffer
        self.acquisitionThread_ = VideoAcquisitionThread(self.spinnakerCamera_, self.videoDisplay_)
        # thread that processes frames and saves them to files.
        self.processingThread_ = VideoProcessingThread(self.spinnakerCamera_)
        #QObject::connect(acquisitionThread_, SIGNAL(frameReady(const QImage &)), &window_, SLOT(setFrame(const QImage &)));
        
    def __del__(self):
        if self.acquisitionOn_:
            self.stopAcquisition()
        del self.acquisitionThread_
        del self.processingThread_
        #del self.videoDisplay_
        #del self.spinnakerCamera_
        print("VideoSingleton deleted!")

    ## inits the camera, gets its name and model to display at the window caption
    def open(self):  
        res = -1
        cameraFullName = None
        if not self.acquisitionOn_:
            res, self.streamProperties_ = self.spinnakerCamera_.initStream();
            if res == 0:
                cameraModel = self.spinnakerCamera_.getModel();
                cameraName = self.spinnakerCamera_.getName();
                if (cameraModel != None) and (cameraName != None):
                    cameraFullName = cameraModel + ", ID " + cameraName;
                #self.videoDisplay_.setWindowTitle(cameraFullName)
        return res, cameraFullName
    
    ## shows the video window and launch both threads
    # input: unsigned long int bufferCapacity
    def startAcquisition(self, bufferCapacity):
        res = -1
        if not self.acquisitionOn_:
            res = self.spinnakerCamera_.start(bufferCapacity)
            if res == 0:
                self.acquisitionOn_ = True;
                #self.window_.setGeometry(100 + cameraIndex_*INITIAL_WINDOW_WIDTH, 100, INITIAL_WINDOW_WIDTH, INITIAL_WINDOW_HEIGHT);
                self.videoDisplay_.Center()
                self.videoDisplay_.Show()
                self.acquisitionThread_.launch(self.streamProperties_, self.DISPLAY_FRAME_RATE);
                self.processingThread_.launch(self.streamProperties_);
        return res
    
    ## stops both threads and close the window
    def stopAcquisition(self):
        self.acquisitionThread_.stop()
        self.videoDisplay_.Close();
        self.processingThread_.stop();
        self.spinnakerCamera_.stop();
        self.acquisitionOn_ = False;

    
    # sets spinnakerCamera_ to capture
    def startRecording(self):
        return self.spinnakerCamera_.startCapture()
    
    # sets spinnakerCamera_ to stop capture
    def stopRecording(self):
        self.spinnakerCamera_.stopCapture()

   
    # input:
    # float frameRate - number of frames acquired per second
    # bool horizFlip - whether the image is flipped around horizontal axis
    # bool vertFlip - whether the image is flipped around vertical axis
    # float exposureTime - length of time when the camera sensor is exposed to light.
    #                      Should be maximal but exposureTime < 1/frameRate
    # float gain - Increase of the camera brightness (equivalent to ISO)
    #              Should be kept low.
    # output: double resultedFrameRate
    def setParameters(self, cameraProperties, displayProperties):
        self.videoDisplay_.setScaling(displayProperties.stretch)
        self.videoDisplay_.setImageRotation(displayProperties.rotation)
        self.videoDisplay_.resize(displayProperties.windowWidth, displayProperties.windowHeight)
        result = self.spinnakerCamera_.setFrameRate(cameraProperties.fps)
        self.spinnakerCamera_.setExposureTime(cameraProperties.exposure)
        self.spinnakerCamera_.setGain(cameraProperties.gain)            
        self.spinnakerCamera_.setHorizontalFlip(cameraProperties.xFlip)
        self.spinnakerCamera_.setVerticalFlip(cameraProperties.yFlip)
        return result


    # output CameraProperties cameraParameters
    def getParameters(self):
        cameraParameters = CameraProperties(fps = self.spinnakerCamera_.getFrameRate(), 
                                            gain = self.spinnakerCamera_.getGain(),
                                            exposure = self.spinnakerCamera_.getExposureTime(),
                                            xFlip = self.spinnakerCamera_.getHorizontalFlip(),
                                            yFlip = self.spinnakerCamera_.getVerticalFlip()
                                            )                       
        return cameraParameters
