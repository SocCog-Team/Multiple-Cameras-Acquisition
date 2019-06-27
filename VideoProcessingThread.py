# -*- coding: utf-8 -*-
"""
Created on Thu Jan  3 14:41:47 2019

A thread saving frames from a queue to a video file. 
Each SpinnakerCamera instance should have own instance of VideoProcessingThread

@author: taskcontroller
"""

import threading
import time
from SpinnakerCamera import SpinnakerCamera

class VideoProcessingThread(threading.Thread):   
    ## input: SpinnakerCamera spinCameraPtr
    def __init__(self, spinCameraPtr): 
        threading.Thread.__init__(self) 
        
        self.stop_ = True
        self.pause_ = False
        
        self.spinnakerCamera_ = spinCameraPtr
        self.numberOfFrames_ = 0
        self.streamProperties_ = None                
        #self.lock_ = threading.Lock()
        #frameSize_ = 0
     
    def __del__(self):
        if not self.stop_:
            self.stop(); 
        del self.spinnakerCamera_    
        print("VideoProcessingThread deleted!")    
 
    ## input: StreamProperties &streamProperties
    def launch(self, streamProperties):
        self.streamProperties_ = streamProperties
        #self.frameSize_ = self.streamProperties_.width*self.streamProperties_.height;
        #if streamProperties_.format == QImage::Format_RGB888:
        #    self.frameSize_*=3;
        #frameBuffer_ = new unsigned char[frameSize_];
        self.stop_ = False;
        self.start();
        
     
    def run(self): 
        framePeriod = 1.0/self.streamProperties_.fps;
        while not self.stop_:
            #self.lock_.release()
            timeStart = time.perf_counter();
            if not self.pause_:
                self.spinnakerCamera_.processFrame() # copy to buffer;
            # compute processing time and wait according to the frame rate
            # we take half of the period to ensure timely responses
            timeElapsed = time.perf_counter() - timeStart;                
            sleepTime = framePeriod/2.0 - timeElapsed;
            if sleepTime > 0:
                time.sleep(sleepTime)
            #self.lock_.acquire()
     
    def stop(self): 
        self.stop_ = True;
        #self.lock_.acquire()
        #del frameBuffer_;
        #self.lock_.release()

    def getFrameRate(self):
        return self.streamProperties_.fps;






