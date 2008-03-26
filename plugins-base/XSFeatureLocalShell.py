# Copyright (c) Citrix Systems 2008. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

if __name__ == "__main__":
    raise Exception("This script is a plugin for xsconsole and cannot run independently")
    
from XSConsoleStandard import *

class XSFeatureLocalShell:
    @classmethod
    def StatusUpdateHandler(cls, inPane):
        inPane.AddTitleField(Lang("Local Command Shell"))
    
        inPane.AddWrappedTextField(Lang(
            "Press <Enter> to start a local command shell on this server.  "
            "This shell will have root privileges."))
    
    @classmethod
    def StartLocalShell(self):
        user = os.environ.get('USER', 'root')
        Layout.Inst().ExitBannerSet(Lang("\rShell for local user '")+user+"'.\r\r"+
                Lang("Type 'exit' to return to the management console.\r"))
        Layout.Inst().SubshellCommandSet("( export TMOUT="+str(State.Inst().AuthTimeoutSeconds())+" && /bin/bash --login )")
        
    @classmethod
    def ActivateHandler(cls):
        DialogueUtils.AuthenticatedOnly(lambda: cls.StartLocalShell())
        
    def Register(self):
        Importer.RegisterNamedPlugIn(
            self,
            'LOCAL_SHELL', # Key of this plugin for replacement, etc.
            {
                'menuname' : 'MENU_ROOT',
                'menupriority' : 1500,
                'menutext' : Lang('Local Command Shell'),
                'statusupdatehandler' : XSFeatureLocalShell.StatusUpdateHandler,
                'activatehandler' : XSFeatureLocalShell.ActivateHandler
            }
        )

# Register this plugin when module is imported
XSFeatureLocalShell().Register()
