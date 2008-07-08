# Copyright (c) Citrix Systems 2008. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

if __name__ == "__main__":
    raise Exception("This script is a plugin for xsconsole and cannot run independently")
    
from XSConsoleStandard import *

class ChangeTimeoutDialogue(InputDialogue):
    def __init__(self):
        self.custom = {
            'title' : Lang("Change Auto-Logout Timeout"),
            'fields' : [ [ Lang("Timeout (minutes)", 20), FirstValue(State.Inst().AuthTimeoutMinutes(), 5), 'timeout', 16 ] ],
            }
        InputDialogue.__init__(self)

    def HandleCommit(self, inValues):
        try:
            timeoutMinutes = int(inValues['timeout'])
        except Exception, e:
            raise Exception("Invalid value - please supply a numeric value")
        
        Auth.Inst().TimeoutSecondsSet(timeoutMinutes * 60)
        return Lang('Timeout Change Successful'), Lang("Timeout changed to ")+inValues['timeout']+Language.Quantity(" minute",  timeoutMinutes)+'.'
        
class XSFeatureChangeTimeout:
    @classmethod
    def StatusUpdateHandler(cls, inPane):
        inPane.AddTitleField(Lang("Change Auto-Logout Time"))
    
        timeout = State.Inst().AuthTimeoutMinutes()
        message = Lang("The current auto-logout time is ") + str(timeout) + " "

        message += Language.Quantity("minute", timeout) + ".  "
        message += Lang("Users will be automatically logged out after there has been no keyboard "
            "activity for this time.  This timeout applies to this console and to "
            "local shells started from this console.")
    
        inPane.AddWrappedTextField(message)
        
        inPane.AddKeyHelpField( { Lang("<Enter>") : Lang("Change Timeout") })

    @classmethod
    def ActivateHandler(cls):
        DialogueUtils.AuthenticatedOnly(lambda: Layout.Inst().PushDialogue(ChangeTimeoutDialogue()))
        
    def Register(self):
        Importer.RegisterNamedPlugIn(
            self,
            'CHANGE_TIMEOUT', # Key of this plugin for replacement, etc.
            {
                'menuname' : 'MENU_AUTH',
                'menupriority' : 300,
                'menutext' : Lang('Change Auto-Logout Time') ,
                'statusupdatehandler' : self.StatusUpdateHandler,
                'activatehandler' : self.ActivateHandler
            }
        )

# Register this plugin when module is imported
XSFeatureChangeTimeout().Register()
