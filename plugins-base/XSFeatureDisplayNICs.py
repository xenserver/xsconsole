# Copyright (c) 2008-2009 Citrix Systems Inc.
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

if __name__ == "__main__":
    raise Exception("This script is a plugin for xsconsole and cannot run independently")
    
from XSConsoleStandard import *

class XSFeatureDisplayNICs:
    @classmethod
    def StatusUpdateHandler(cls, inPane):
        data = Data.Inst()
        
        inPane.AddTitleField(Lang("Network Interfaces"))
        
        for pif in data.host.PIFs([]):
            inPane.AddWrappedBoldTextField(pif['metrics']['device_name'])
            if pif['metrics']['carrier']:
                inPane.AddWrappedTextField(Lang("(connected)"))
            else:
                inPane.AddWrappedTextField(Lang("(not connected)"))
                
            inPane.AddStatusField(Lang("MAC Address", 16), pif['MAC'])
            inPane.AddStatusField(Lang("Device", 16), pif['device'])
            inPane.NewLine()
        
    def Register(self):
        Importer.RegisterNamedPlugIn(
            self,
            'DISPLAY_NICS', # Key of this plugin for replacement, etc.
            {
                'menuname' : 'MENU_NETWORK',
                'menupriority' : 700,
                'menutext' : Lang('Display NICs'),
                'statusupdatehandler' : XSFeatureDisplayNICs.StatusUpdateHandler
            }
        )

# Register this plugin when module is imported
XSFeatureDisplayNICs().Register()
