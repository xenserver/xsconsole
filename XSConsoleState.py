# Copyright (c) Citrix Systems 2007. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

import re, os, pickle

from XSConsoleBases import *
from XSConsoleLang import *

class State:
    instance = None
    savePath = '/etc/xsconsole'
    saveLeafname = 'state.txt'
    thisVersion = 9
    
    #***
    #*** Increment thisVersion (above) when adding attributes to this object
    #***
    def __init__(self):
        self.version = self.thisVersion
        self.authTimeoutSeconds = 5*60
        self.passwordChangeRequired = False # IsPasswordSet now takes care of this
        self.modified = True
        self.rebootMessage = None
        self.weStoppedXAPI = False
        self.verboseBoot = False
        self.keymap = None
        self.sleepSeconds = 30*60
        
    @classmethod
    def SaveFilename(self):
        return self.savePath+'/'+self.saveLeafname
        
    @classmethod
    def Inst(cls):
        # Load the saved state if we can, otherwise create a default object
        if cls.instance is None:
            isFirstBoot = True
            try:
                if os.path.isfile(cls.SaveFilename()):
                    saveFile = open(cls.SaveFilename(), "r")
                    unpickler = pickle.Unpickler(saveFile)
                    cls.instance = unpickler.load()
                    saveFile.close()
                    isFirstBoot = False
                    if cls.instance.version != cls.instance.thisVersion:
                        # Version mismatch - don't use the state information
                        cls.instance = None
            except Exception, e:
                cls.instance = None
            
            if cls.instance is None:
                cls.instance = State()
            
            # Fill in pseudo-state
            cls.instance.isFirstBoot = isFirstBoot
            cls.instance.MakeSane()
            
        return cls.instance
        
    def AuthTimeoutSeconds(self):
        return self.authTimeoutSeconds
        
    def PasswordChangeRequired(self):
        return self.passwordChangeRequired
        
    def PasswordChangeRequiredSet(self, inValue):
        self.passwordChangeRequired = inValue
        self.modified = True
    
    def RebootMessage(self):
        return self.rebootMessage
        
    def RebootMessageSet(self, inValue):
        self.rebootMessage = inValue
        self.modified = True
    
    def VerboseBoot(self):
        return self.verboseBoot
        
    def VerboseBootSet(self, inValue):
        self.verboseBoot = inValue
        self.modified = True
    
    def Keymap(self):
        return self.keymap
        
    def KeymapSet(self, inValue):
        self.keymap = inValue
        self.modified = True

    def IsFirstBoot(self):
        return self.isFirstBoot
    
    def WeStoppedXAPI(self):
        return self.weStoppedXAPI
        
    def WeStoppedXAPISet(self, inValue):
        self.weStoppedXAPI = inValue
        self.modified = True

    def AuthTimeoutSecondsSet(self, inSeconds): # Don't call this directly - use Auth.TimeoutSecondsSet
        if inSeconds < 60:
            raise Exception("Cannot set a session timeout of less than one minute")
        if self.authTimeoutSeconds != inSeconds:
            self.authTimeoutSeconds = inSeconds
            self.modified = True
        
    def AuthTimeoutMinutes(self):
        return int((self.AuthTimeoutSeconds() + 30) / 60)
    
    def SleepSeconds(self):
        return self.sleepSeconds
    
    def MakeSane(self):
        self.authTimeoutSeconds = int(self.authTimeoutSeconds)
        if self.authTimeoutSeconds < 60:
            AuthTimeoutSecondsSet(60)
    
    def SaveIfRequired(self):
        self.MakeSane()
        try:
            if not os.path.isdir(self.savePath):
                os.mkdir(self.savePath, 0700)
            
            saveFile = open(self.SaveFilename(), "w")
            pickler = pickle.Pickler(saveFile)
            self.modified = False # Set unmodified before saving
            pickler.dump(self)
            saveFile.close()
        except Exception, e:
            pass # Ignore failure


