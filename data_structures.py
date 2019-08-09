# -*- coding: utf-8 -*-
"""
Created on Fri Jan 11 17:21:19 2019

@author: taskcontroller
"""
from collections import namedtuple 

class ImageFormat:
    RGB24 = 'RGB'
    MONO8 = 'L'
    Mono16 = 'Mono16'
    YCbCr = 'YCbCr'

class StreamProperties: 
    def __init__(self, width, height, fps, imageFormat = ImageFormat.MONO8):
        self.width = width
        self.height = height 
        self.fps = fps
        self.format = imageFormat
        
    def getFrameSize(self):
        frameSize = self.width*self.height
        if self.format == ImageFormat.RGB24:
            frameSize *= 3
        if self.format == ImageFormat.YCbCr:
            frameSize *= 3
        frameSize += 512 # for non-standart frame sizes
        return frameSize      
    

class CameraProperties(namedtuple('CameraProperties', ['fps', 'gain', 'exposure', 'xFlip', 'yFlip', 'pixelFormat'])):
    def __new__(cls, fps = 25.0, gain = 0.0, exposure = 39000.0, 
                       xFlip = False, yFlip = False, pixelFormat = 'Mono8'):
        try:
            fps = float(fps)
        except ValueError:
            raise ValueError('fps value ' + str(fps) + ' in ini-file has incorrect format!') 
            
        try:
            gain = float(gain)
        except ValueError:
            raise ValueError('gain value ' + str(gain) + ' in ini-file has incorrect format!') 
        
        try:
            exposure = float(exposure)
        except ValueError:
            raise ValueError('exposure value ' + str(exposure) + ' in ini-file has incorrect format!') 
        if exposure*fps >= 10**7:
            raise ValueError('exposure value ' + str(exposure) + ' in ini-file is too large! Should be below ' + str(10.0**7/fps)) 
        
        try:
            xFlip = bool(xFlip)
        except ValueError:
            raise ValueError('xFlip value ' + str(xFlip) + ' in ini-file has incorrect format!') 

        try:
            yFlip = bool(yFlip)
        except ValueError:
            raise ValueError('yFlip value ' + str(yFlip) + ' in ini-file has incorrect format!')  
            
        try:
            pixelFormat = str(pixelFormat)
        except ValueError:
            raise ValueError('pixelFormat value ' + str(pixelFormat) + ' in ini-file has incorrect format!')  
            
        self = super().__new__(cls, fps, gain, exposure, xFlip, yFlip, pixelFormat)
        return self
        
        
class DisplayProperties(namedtuple('DisplayProperties', ['stretch', 'rotation', 'windowWidth', 'windowHeight', 'pixelFormat'])): 
    def __new__(cls, stretch = True, rotation = 0, windowWidth = 1280, windowHeight = 1024, pixelFormat = 'Mono8'):
        try:
            stretch = bool(stretch)
        except ValueError:
            raise ValueError('stretch value ' + str(stretch) + ' in ini-file has incorrect format!') 

        try:
            rotation = int(rotation)
        except ValueError:
            raise ValueError('rotation value ' + str(rotation) + ' in ini-file has incorrect format!')         

        try:
            windowWidth = int(windowWidth)
        except ValueError:
            raise ValueError('windowWidth value ' + str(windowWidth) + ' in ini-file has incorrect format!')  

        try:
            windowHeight = int(windowHeight)
        except ValueError:
            raise ValueError('windowHeight value ' + str(windowHeight) + ' in ini-file has incorrect format!')
            
        try:
            pixelFormat = str(pixelFormat)
        except ValueError:
            raise ValueError('pixelFormat value ' + str(pixelFormat) + ' in ini-file has incorrect format!')              
            
        self = super().__new__(cls, stretch, rotation, windowWidth, windowHeight, pixelFormat)
        return self
    
    
class CaptureProperties(namedtuple('CaptureProperties', ['pixelFormat', 'outputPath', 'cameraPrefix', 'cameraSuffix', 'aviType', 'MJPGQuality', 'H264BitRate'])):
    def __new__(cls, pixelFormat = 'Mono8', outputPath = 'D:/', cameraPrefix = 'Camera_', cameraSuffix = '', aviType = 'MJPG', MJPGQuality = 75, H264BitRate = 1000000):            
        try:
            pixelFormat = str(pixelFormat)
        except ValueError:
            raise ValueError('pixelFormat value ' + str(pixelFormat) + ' in ini-file has incorrect format!')              

        try:
            outputPath = str(outputPath)
        except ValueError:
            raise ValueError('outputPath value ' + str(outputPath) + ' in ini-file has incorrect format!')  

        try:
            cameraPrefix = str(cameraPrefix)
        except ValueError:
            raise ValueError('cameraPrefix value ' + str(cameraPrefix) + ' in ini-file has incorrect format!')  

        try:
            cameraSuffix = str(cameraSuffix)
        except ValueError:
            raise ValueError('cameraSuffix value ' + str(cameraSuffix) + ' in ini-file has incorrect format!')              

        try:
            aviType = str(aviType)
        except ValueError:
            raise ValueError('aviType value ' + str(aviType) + ' in ini-file has incorrect format!')

        try:
            MJPGQuality = int(MJPGQuality)
        except ValueError:
            raise ValueError('MJPGQuality value ' + str(MJPGQuality) + ' in ini-file has incorrect format!')                    

        try:
            H264BitRate = int(H264BitRate)
        except ValueError:
            raise ValueError('H264BitRate value ' + str(H264BitRate) + ' in ini-file has incorrect format!')                    
          
        self = super().__new__(cls, pixelFormat, outputPath, cameraPrefix, cameraSuffix, aviType, MJPGQuality, H264BitRate)
        return self
            
    
class TriggerProperties(namedtuple('TriggerProperties', ['triggerMode', 'triggerSource', 'triggerOverlap', 'triggerActivation'])):
    def __new__(cls, triggerMode = 'TriggerMode_Off', triggerSource = 'LineSource_Line3', triggerOverlap = 'TriggerOverlap_ReadOut', triggerActivation = 'TriggerActivation_FallingEdge'):            
        try:
            triggerMode = str(triggerMode)
        except ValueError:
            raise ValueError('triggerMode value ' + str(triggerMode) + ' in ini-file has incorrect format!')              

        try:
            triggerSource = str(triggerSource)
        except ValueError:
            raise ValueError('triggerSource value ' + str(triggerSource) + ' in ini-file has incorrect format!')  

        try:
            triggerOverlap = str(triggerOverlap)
        except ValueError:
            raise ValueError('triggerOverlap value ' + str(triggerOverlap) + ' in ini-file has incorrect format!')  

        try:
            triggerActivation = str(triggerActivation)
        except ValueError:
            raise ValueError('triggerActivation value ' + str(triggerActivation) + ' in ini-file has incorrect format!')              

          
        self = super().__new__(cls, triggerMode, triggerSource, triggerOverlap, triggerActivation)
        return self    