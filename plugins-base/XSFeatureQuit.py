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

class XSFeatureQuit:
    @classmethod
    def StatusUpdateHandler(cls, inPane):
        inPane.AddTitleField(Lang("Quit"))
    
        inPane.AddWrappedTextField(Lang(
            "Press <Enter> to quit this console."))

    @classmethod
    def ActivateHandler(cls):
        Layout.Inst().ExitBannerSet(Lang("Quitting..."))
        Layout.Inst().ExitCommandSet('') # Just exit
        
    def Register(self):
        # When started from inittab, mingetty adds -f root to the command, so use this to suppress the Quit choice
        if not '-f' in sys.argv:
            Importer.RegisterNamedPlugIn(
                self,
                'Quit', # Key of this plugin for replacement, etc.
                {
                    'menuname' : 'MENU_ROOT',
                    'menupriority' : 10000,
                    'menutext' : Lang('Quit'),
                    'statusupdatehandler' : XSFeatureQuit.StatusUpdateHandler,
                    'activatehandler' : XSFeatureQuit.ActivateHandler
                }
            )

# Register this plugin when module is imported
XSFeatureQuit().Register()
