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
            'fg_dark' : (444, 444, 333),
            'fg_normal' : (666, 666, 500),
            'fg_bright' : (999, 999, 750),
            'bg_dark' : (0, 0, 0), 
            'bg_normal' : (333, 0, 0), 
            'bg_bright' : (500, 0, 0), 
            
            # Recovery mode colours
            'recovery_fg_dark' : (444, 444, 333),
            'recovery_fg_normal' : (666, 666, 500),
            'recovery_fg_bright' : (999, 999, 750),
            'recovery_bg_dark' : (0, 0, 0), 
            'recovery_bg_normal' : (0, 150, 200), 
            'recovery_bg_bright' : (0, 200, 266)
        }
        
        self.ftpname = 'XenServer Support'
        self.ftpserver = 'ftp://support.xensource.com/'
    
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
    
# Import a more specific configuration if available
if os.path.isfile(sys.path[0]+'/XSConsoleConfigOEM.py'):
    import XSConsoleConfigOEM
    
