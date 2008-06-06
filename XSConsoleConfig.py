# Copyright (c) Citrix Systems 2007. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

import os, sys

class Config:
    instance = None
    
    def __init__(self):
        self.colours = {
            # Colours specified as name : (red, green, blue), value range 0..999
            'fg_dark' : (400, 400, 360),
            'fg_normal' : (600, 600, 550),
            'fg_bright' : (999, 999, 800),
            'bg_dark' : (0, 0, 0), 
            'bg_normal' : (0, 168, 325), 
            'bg_bright' : (0, 200, 400), 
        }
        
        self.ftpname = 'XenServer Support'
        self.ftpserver = 'ftp://support.xensource.com/bugreports'
    
    @classmethod
    def Inst(cls):
        if cls.instance is None:
            cls.instance = Config()
        return cls.instance
    
    @classmethod
    def Mutate(cls, inConfig):
        cls.instance = inConfig
    
    def Colour(self,  inName):
        return self.colours[inName]
    
    def FTPName(self):
        return self.ftpname
        
    def FTPServer(self):
        return self.ftpserver
    
    def BrandingMap(self):
        return {}
        
    
# Import a more specific configuration if available
if os.path.isfile(sys.path[0]+'/XSConsoleConfigOEM.py'):
    import XSConsoleConfigOEM
    
