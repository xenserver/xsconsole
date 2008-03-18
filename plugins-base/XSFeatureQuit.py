# Copyright (c) Citrix Systems 2008. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

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
