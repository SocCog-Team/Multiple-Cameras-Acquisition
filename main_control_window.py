# -*- coding: utf-8 -*-
"""
Created on Tue Jan  8 09:24:35 2019

@author: taskcontroller
"""

from SpinnakerControl import SpinnakerControl
from acquisition_ini import AcquisitionINI

import wx

class MainWindow(wx.Frame):
    def __init__(self, title):
        wx.Frame.__init__(self, None, title=title, pos=(150,150), size=(350,200))
        self.Bind(wx.EVT_CLOSE, self.onClose)

        menuBar = wx.MenuBar()
        menu = wx.Menu()
        mExit = menu.Append(wx.ID_EXIT, "E&xit\tAlt-X", "Close window and exit program.")
        self.Bind(wx.EVT_MENU, self.onClose, mExit)
        menuBar.Append(menu, "&File")
        self.SetMenuBar(menuBar)
        
        self.statusbar_ = self.CreateStatusBar()

        panel = wx.Panel(self)
        box = wx.BoxSizer(wx.VERTICAL)
         
        self.recordingBtn_ = wx.ToggleButton(panel, label = "Start recording")
        self.recordingBtn_.Bind(wx.EVT_TOGGLEBUTTON, self.onToggleRecording)
        self.recordingOn_ = False
        self.recordingBtn_.SetValue(False) 
        box.Add(self.recordingBtn_, 0, wx.ALL, 10)
        
        panel.SetSizer(box)
        panel.Layout()
        
    def onClose(self, event):
        dlg = wx.MessageDialog(self, 
            "Do you really want to close this application?",
            "Confirm Exit", wx.OK|wx.CANCEL|wx.ICON_QUESTION)
        result = dlg.ShowModal()
        dlg.Destroy()
        if result == wx.ID_OK:
            self.Destroy() 
            del self.statusbar_
            del self.recordingBtn_
            return True
        return False
    
    def onToggleRecording(self, event):
        btn = event.GetEventObject()
        recordingOn = btn.GetValue() 
        if recordingOn: # if new state is 'recording on'
            btn.SetLabel("Stop recording")
        else:    
            btn.SetLabel("Start recording")
        return recordingOn  


class VideoAcquisitionControl(MainWindow):
    def __init__(self, title):
        #app = wx.App(redirect=True)
        super().__init__(title)
        self.videoControl_ = SpinnakerControl()  
        self.iniFile_ = AcquisitionINI()
        self.numCameras_ = 0 
        self.recordingOn_ = False
        self.acquisitionOn_ = False

       
    def launch(self): 
        self.iniFile_.load()
        self.numCameras_ = self.videoControl_.initCameras() 
        if self.numCameras_ > 0:
            
            self.loadSettings()
            self.videoControl_.startAcquisition()
            self.acquisitionOn_ = True
        else:
            self.recordingBtn_.Disable()
         
                  
    #def onToggleAquisition(self):        
    #    if self.acquisitionOn_:
    #        self.videoControl_.stopAcquisition() 
    #    else:
    #        self.videoControl_.startAcquisition() 
        
    def onToggleRecording(self, event):    
        self.recordingOn_ = super().onToggleRecording(event)    
        if self.recordingOn_:
            self.videoControl_.startRecording() 
        else:
            self.videoControl_.stopRecording() 
    
#    def triggerToggleRecording(self):                
#        event = wx.PyCommandEvent(wx.EVT_BUTTON.typeId, self.GetId())
#        wx.PostEvent(self.GetEventHandler(), event)
     
    def onClose(self, event):        
        if super().onClose(event):   # if we really need to close      
            if self.recordingOn_:
                self.videoControl_.stopRecording() 
            if self.acquisitionOn_:
                self.videoControl_.stopAcquisition()     
            self.videoControl_.close() 
            del self.videoControl_ 
            del self.iniFile_
            print("Main window closed.")

    def loadSettings(self):          
        for i in range(0,self.numCameras_):
            cameraName = self.videoControl_.names_[i]
            cameraProperties = self.iniFile_.getCameraProperties(cameraName)
            displayProperties = self.iniFile_.getDisplayProperties(cameraName)
            self.videoControl_.setParameters(i, cameraProperties, displayProperties)              