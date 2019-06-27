# -*- coding: utf-8 -*-
"""
Created on Mon Jan  7 15:02:08 2019

@author: taskcontroller
This file defines window and graphical elements for the output of the acquired 
video using wxPython toolkit and PIL image class (for the color format transformation)
class VideoDisplay defines a window for displaying the acquired frames:
class VideoPanel defines a graphical panel for displaying the acquired frames
"""

import wx
from PIL import Image

# set of constants defining possible rotations of the displayed video
class ImageRotation:
    ANGLE0 = 0
    ANGLE90 = 90
    ANGLE180 = 180
    ANGLE270 = 270

# default size of video panel
DEFAULT_SIZE = (640, 480)

# panel (graphical element) for displaying the acquired frames, is used as a 
# of VideoDisplay class to DELEGATE part of its functionality.
# inherited from a standard wx panel (wx.Panel) 
class VideoPanel(wx.Panel):       
    def __init__(self, parent):
        super().__init__(parent, -1)
        self.SetSize(DEFAULT_SIZE)
        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
        self.Bind(wx.EVT_PAINT, self.onPaint)
        self.bitmap_ = None
        self.needScale_ = False
        self.rotationAngle_ = 0
        self.updateForbidden_ = False
        self.update()
            
    def update(self):
        if self.updateForbidden_:
            return 0
        #print("Update called!")
        self.Refresh()
        self.Update()
        wx.CallLater(15, self.update)

    def scaleToWindow(self, bitmap):
        image = bitmap.ConvertToImage()
        (width, height) = self.GetSize()
        image = image.Scale(width, height, wx.IMAGE_QUALITY_HIGH)
        scaledBitmap = wx.Bitmap(image)
        return scaledBitmap

    def showNew(self, width, height, buffer, isRGB = True):
        if isRGB:
            newBitmap = wx.Bitmap.FromBuffer(width, height, buffer)                                    
            if self.rotationAngle_ != ImageRotation.ANGLE0:
                rotatedImage = self.rotate(newBitmap.ConvertToImage())
                newBitmap = rotatedImage.ConvertToBitmap()
        else: 
            imageMono = Image.frombuffer('L', (width, height), buffer, 'raw', 'L', 0, 1)
            if self.rotationAngle_ != ImageRotation.ANGLE0:
                imageMono = self.rotate(imageMono)   
            bufferRGB = imageMono.convert('RGB').tobytes()
            newBitmap = wx.Bitmap.FromBuffer(width, height, bufferRGB)
        if self.needScale_:            
            self.bitmap_ = self.scaleToWindow(newBitmap)
        else:
            self.bitmap_ = newBitmap
            #self.bitmap_ = wx.BitmapFromBuffer(width, height, buffer)
        self.Update()
    
    def onPaint(self, event):
        if self.bitmap_ != None:
            dc = wx.AutoBufferedPaintDC(self)
            dc.DrawBitmap(self.bitmap_, 0, 0)                
    
    def rotate(self, image):
        if self.rotationAngle_ == ImageRotation.ANGLE90:
            rotatedImage = image.Rotate90()           
        elif self.rotationAngle_ == ImageRotation.ANGLE180 or self.rotationAngle_ == ImageRotation.ANGLE270:
            rotatedImage = image.Rotate180()
            if self.rotationAngle_ == ImageRotation.ANGLE270:
                rotatedImage = rotatedImage.Rotate90()
        return rotatedImage  


# window for displaying the acquired frames
# inherited from a standard wx video (wx.Frame) 
class VideoDisplay(wx.Frame):
    def __init__(self):
        style = wx.DEFAULT_FRAME_STYLE & (~wx.RESIZE_BORDER) & (~wx.CLOSE_BOX) & (~wx.MAXIMIZE_BOX)
        super().__init__(None, -1, 'Camera Viewer', style=style)
        
        self.Bind(wx.EVT_CLOSE, self.onClose)
        self.panel_ = VideoPanel(self)
        self.Fit()
        
    def onClose(self, event):
        self.panel_.updateForbidden_ = True  
        self.Destroy()       
    
    def showRGB(self, width, height, buffer):
        if self.panel_ != None:
            self.panel_.showNew(width, height, buffer, isRGB = True)


    def showMono(self, width, height, buffer):
        if self.panel_ != None:
            self.panel_.showNew(width, height, buffer, isRGB = False)
        
    def setScaling(self, needScale):
        if self.panel_ != None:
            self.panel_.needScale_ = needScale 

    def setImageRotation(self, rotationAngle):
        if self.panel_ != None:
            self.panel_.rotationAngle_ = rotationAngle        

            
    def resize(self, width, height):
        if self.panel_ != None:
            self.panel_.SetSize((width, height))  
            self.SetClientSize((width, height)) 
        
   
        