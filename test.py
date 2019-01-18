# -*- coding: utf-8 -*-
"""
Created on Thu Jan  3 12:47:34 2019

@author: taskcontroller
"""
import wx
from main_control_window import VideoAcquisitionControl 

def main():
    app = wx.App()   
    mainWindow = VideoAcquisitionControl("Video Acquistion Control Window")
    mainWindow.launch()
    mainWindow.Show()
    app.MainLoop() 
    del app

if __name__ == '__main__':
    main()
    