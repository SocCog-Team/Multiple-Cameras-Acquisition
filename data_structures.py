# -*- coding: utf-8 -*-
"""
Created on Fri Jan 11 17:21:19 2019

@author: taskcontroller
"""
from collections import namedtuple 

class ImageFormat:
    RGB24 = 'RGB'
    MONO8 = 'L'    

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
        frameSize += 512 # for non-standart frame sizes
        return frameSize      
    

class CameraProperties(namedtuple('CameraProperties', ['fps', 'gain', 'exposure', 'xFlip', 'yFlip'])):
    def __new__(cls, fps = 25.0, gain = 0.0, exposure = 39000.0, 
                       xFlip = False, yFlip = False):
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
        self = super().__new__(cls, fps, gain, exposure, xFlip, yFlip)
        return self
        
        
class DisplayProperties(namedtuple('DisplayProperties', ['stretch', 'rotation', 'windowWidth', 'windowHeight'])): 
    def __new__(cls, stretch = True, rotation = 0, windowWidth = 640, windowHeight = 480):
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
        self = super().__new__(cls, stretch, rotation, windowWidth, windowHeight)
        return self
     