# -*- coding: utf-8 -*-
"""
Created on Fri Jan 11 14:22:12 2019
class for reading/writing cameras configurations and display settings to ini file
@author: taskcontroller
"""
import configparser
from data_structures import CameraProperties, DisplayProperties

class AcquisitionINI:
    def __init__(self):
        self.filename_ = "acquisition.ini"
        self.defaultSectionTitle_ = 'Default'
        self.cameraSubsectionTitle_ = 'Camera'
        self.displaySubsectionTitle_ = 'Display'
        
        self.config_ = configparser.RawConfigParser()
        self.config_.optionxform = lambda option: option # switch to case-preserving mode 


    def __del__(self): 
        del self.config_


    def checkAndRecreateSection(self, deviceName, subsection):
        sectionFullName = deviceName + ", " + subsection
        recreateSection = False
        if self.config_.has_section(sectionFullName):
            labels, entries = zip(*self.config_.items(sectionFullName))                       
            if subsection == self.cameraSubsectionTitle_: 
                correctLabels = CameraProperties._fields
            elif subsection == self.displaySubsectionTitle_:             
                correctLabels = DisplayProperties._fields
            else:
                correctLabels = []   
            if labels != correctLabels:   
                self.config_.remove_section(sectionFullName)
                print('Error in section %s of ini-file, recreated' %sectionFullName)
                recreateSection = True
        else:
             recreateSection = True
            
        if recreateSection:
            self.config_.add_section(sectionFullName)
            if subsection == self.cameraSubsectionTitle_:   # if Camera subsection is absent ...
                if deviceName == self.defaultSectionTitle_: # ... for default section - recreate
                    defaultProperties = CameraProperties()   
                else:                                       # ... otherwise - copy from default section
                    defaultProperties = self.getCameraProperties(self.defaultSectionTitle_)
            elif subsection == self.displaySubsectionTitle_:# if Camera subsection is absent ...
                if deviceName == self.defaultSectionTitle_: # ... for default section - recreate
                    defaultProperties = DisplayProperties()
                else:                                       # ... otherwise - copy from default section
                    defaultProperties = self.getDisplayProperties(self.defaultSectionTitle_)
            
            iniFileLabels = defaultProperties._fields
            iniFileEntries = list(defaultProperties)
            for label, entry in zip(iniFileLabels, iniFileEntries):
                # zip stops when the shorter of iniFileLabels or iniFileEntries stops.
                self.config_.set(sectionFullName, label, str(entry))
                #print(label + ", " + str(entry))
            
            # write config data to the file
            cfgfile = open(self.filename_,'w')
            self.config_.write(cfgfile)
            cfgfile.close()
        return sectionFullName    
        
                       
    def load(self):  
        self.config_.read(self.filename_) 
        if not self.config_:
            print('No INI file found, recreated')
        self.checkAndRecreateSection(self.defaultSectionTitle_, self.cameraSubsectionTitle_)
        self.checkAndRecreateSection(self.defaultSectionTitle_, self.displaySubsectionTitle_)        
        
    
    # Returns a list of camera options  
    def getProperties(self, deviceName, subsection):
        # check whether section exists and get full section name from deviceName
        sectionFullName = self.checkAndRecreateSection(deviceName, subsection)           
        
        labels, entries = zip(*self.config_.items(sectionFullName))     
        print(entries) 
        if subsection == self.cameraSubsectionTitle_: 
            properties = CameraProperties(*entries)
        elif subsection == self.displaySubsectionTitle_:             
            properties = DisplayProperties(*entries) 
        else:
            properties = None
            
        print(entries)    
        return properties


    # Returns a namedtuple of camera properties  
    def getCameraProperties(self, deviceName):
        return self.getProperties(deviceName, self.cameraSubsectionTitle_)
    
    # Returns a namedtuple of display options  
    def getDisplayProperties(self, deviceName):
        return self.getProperties(deviceName, self.displaySubsectionTitle_)
            