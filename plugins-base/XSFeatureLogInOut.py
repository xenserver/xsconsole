# Copyright (c) Citrix Systems 2008. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

if __name__ == "__main__":
    raise Exception("This script is a plugin for xsconsole and cannot run independently")
    
from XSConsoleStandard import *

class XSFeatureLogInOut:
    @classmethod
    def StatusUpdateHandler(cls, inPane):
        if Auth.Inst().IsAuthenticated():
            inPane.AddTitleField(Lang("Log Out"))
            inPane.AddWrappedTextField(Lang("Press <Enter> to log out."))
            inPane.AddKeyHelpField( {Lang("<Enter>") : Lang("Log out") })
        else:
            inPane.AddTitleField(Lang("Log In"))
            inPane.AddWrappedTextField(Lang("Press <Enter> to log in."))
            inPane.AddKeyHelpField( { Lang("<Enter>") : Lang("Log in") })

    @classmethod
    def ActivateHandler(cls):
        if Auth.Inst().IsAuthenticated():
            name = Auth.Inst().LoggedInUsername()
            Auth.Inst().LogOut()
            Data.Inst().Update()
            Layout.Inst().PushDialogue(InfoDialogue( Lang("User '")+name+Lang("' logged out")))
        else:
            Layout.Inst().PushDialogue(LoginDialogue())

    def Register(self):
        Importer.RegisterNamedPlugIn(
            self,
            'LOGINOUT', # Key of this plugin for replacement, etc.
            {
                'menuname' : 'MENU_AUTH',
                'menupriority' : 100,
                'menutext' : Lang('Log In/Out'),
                'statusupdatehandler' : XSFeatureLogInOut.StatusUpdateHandler,
                'activatehandler' : XSFeatureLogInOut.ActivateHandler
            }
        )

# Register this plugin when module is imported
XSFeatureLogInOut().Register()
