# Copyright (c) 2007-2009 Citrix Systems Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 only.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

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
        
        self.ftpserver = ''

        self.xcpconfigdir = ''
        for path in ["/etc/xcp", "/etc/xensource"]:
            if os.path.exists(path):
                self.xcpconfigdir = path
                break

        self.xecli = '/usr/bin/xe'
        for path in ["/usr/bin/xe", "/opt/xensource/bin/xe"]:
            if os.path.exists(path):
                self.xecli = path

        self.helperdir = ''
        for path in ["/usr/lib/xcp/bin", "/opt/xensource/bin"]:
            if os.path.exists(path):
                self.helperdir = path
                break
    
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
    
    def FTPServer(self):
        return self.ftpserver
    
    def BrandingMap(self):
        return {}
    
    def AllShellsTimeout(self):
        return True
    
    def DisplaySerialNumber(self):
        return True
        
    def DisplayAssetTag(self):
        return True
    
    def BMCName(self):
        return 'BMC'
        
    def FirstBootEULAs(self):
        # Subclasses in XSConsoleConfigOEM can add their EULAs to this array
        return ['/EULA']

    def XCPConfigDir(self):
        return self.xcpconfigdir

    def XECLIPath(self):
        return self.xecli

    def HelperPath(self):
        return self.helperdir

# Import a more specific configuration if available
if os.path.isfile(sys.path[0]+'/XSConsoleConfigOEM.py'):
    import XSConsoleConfigOEM
    
