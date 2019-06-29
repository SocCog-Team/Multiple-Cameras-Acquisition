# -*- coding: utf-8 -*-
"""
Created on Fri Jan  4 09:27:07 2019

Thread acquiring frames from the camera. It puts each frame 
to a queue for saving to video file and to a buffer for displaying. 
Each SpinnakerCamera instance should have own instance of VideoAcquisitionThread

@author: taskcontroller
"""

import threading
import time
from SpinnakerCamera import SpinnakerCamera
from data_structures import ImageFormat
from PIL import Image
from wxWindow import VideoDisplay

class VideoAcquisitionThread(threading.Thread):   
    ## input: SpinnakerCamera spinCameraPtr
    def __init__(self, spinCameraPtr, videoDisplay): 
        threading.Thread.__init__(self) 
        
        self.stop_ = True
        self.pause_ = False
        
        self.spinnakerCamera_ = spinCameraPtr
        self.videoDisplay_ = videoDisplay
        #self.lock_ = threading.Lock()
        #frameSize_ = 0
     
    def __del__(self):
        if not self.stop_:
            self.stop()
        self.videoDisplay_.Close()    
        #del self.videoDisplay_
        del self.spinnakerCamera_
        print("VideoAcquisitionThread deleted!")    
 
    ## input: StreamProperties &streamProperties, int displayFrameRate
    def launch(self, streamProperties, displayFrameRate):
        self.streamProperties_ = streamProperties
        self.displayFrameRate_ = displayFrameRate;
        #self.frameSize_ = self.streamProperties.getFrameSize();
        #self.frameBuffer_ = new unsigned char[frameSize_];
        
        self.stop_ = False;
        self.start();
        
     
    def run(self): 
        framePeriod = 1.0/self.streamProperties_.fps
        frameCntMax = self.streamProperties_.fps/self.displayFrameRate_
        frameCnt = frameCntMax;
        while not self.stop_:
            #self.lock_.acquire()
            timeStart = time.perf_counter();
            if not self.pause_:
                # process frame if necessary
                if frameCnt <= 0:
                    frameCnt = frameCntMax;
                    # put the frame to queue for recording and to buffer for displaying
                    result, self.frameBuffer_ = self.spinnakerCamera_.acquireFrames(True)
                    #self.spinnakerCamera_.processFrame()
                    if result == 0:
                        #print('self.spinnakerCamera_.cameraProperties.pixelFormat: %s' % self.spinnakerCamera_.cameraProperties.pixelFormat)
                        # any color conversion for display purposes needs to go here
                        
#                        # convert image?
#                        if self.spinnakerCamera_.PySpin_DisplayPixelFormatString != self.spinnakerCamera_.requested_pixelformat:
#                            self.frameBuffer_ = self.frameBuffer_.frame.Convert(self.PySpin_DisplayPixelFormat, PySpin.HQ_LINEAR)
                        
                        self.videoDisplay_.showByPixelFormat(self.spinnakerCamera_.PySpin_DisplayPixelFormatString , self.streamProperties_.width, self.streamProperties_.height, self.frameBuffer_)
                        
                        
#                        if self.streamProperties_.format == ImageFormat.RGB24:
#                            self.videoDisplay_.showRGB(self.streamProperties_.width, self.streamProperties_.height, self.frameBuffer_)
#                        elif self.streamProperties_.format == ImageFormat.YCbCr:
#                            self.videoDisplay_.showCbYCr(self.streamProperties_.width, self.streamProperties_.height, self.frameBuffer_)
#                        else:
#                            self.videoDisplay_.showMono(self.streamProperties_.width, self.streamProperties_.height, self.frameBuffer_)
                        #image = Image.frombytes(self.streamProperties_.format, (self.streamProperties_.width, self.streamProperties_.height), self.frameBuffer_, 'raw')
                        #BitmapFromBuffer(self.streamProperties_.width, self.streamProperties_.height, self.frameBuffer_)
                        #image.show()
                    #!!Image image = QImage(frameBuffer_, streamProperties_.width, streamProperties_.height, streamProperties_.format);
                    #!!emit frameReady(image);    // emit QImage to the MainWindow object
                else:
                    # just put the frame to queue without displaying
                    self.spinnakerCamera_.acquireFrames(False); 
                frameCnt -= 1
            # compute processing time and wait according to the frame rate
            # we take half of the period to ensure timely responses
            timeElapsed = time.perf_counter() - timeStart;                
            sleepTime = framePeriod - timeElapsed;
            if sleepTime > 0:
                time.sleep(sleepTime)
            #self.lock_.release()

     
    def stop(self): 
        self.stop_ = True;
        #self.lock_.acquire()
        #del frameBuffer_;
        #self.lock_.release()



