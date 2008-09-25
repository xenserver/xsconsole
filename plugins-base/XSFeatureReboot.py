# Copyright (c) Citrix Systems 2008. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

if __name__ == "__main__":
    raise Exception("This script is a plugin for xsconsole and cannot run independently")
    
from XSConsoleStandard import *

class XSFeatureReboot:
    @classmethod
    def StatusUpdateHandler(cls, inPane):
        inPane.AddTitleField(Lang("Reboot Server"))
    
        inPane.AddWrappedTextField(Lang(
            "Press <Enter> to reboot this server."))
    
        inPane.AddKeyHelpField( {
            Lang("<Enter>") : Lang("Reboot Server")
        } )

    @classmethod
    def RebootReplyHandler(cls,  inYesNo):
        if inYesNo == 'y':
            try:
                Data.Inst().LocalHostDisable()
                Layout.Inst().ExitBannerSet(Lang("Rebooting..."))
                Layout.Inst().ExitCommandSet('/sbin/shutdown -r now')
            except Exception, e:
                Layout.Inst().PushDialogue(InfoDialogue(Lang("Reboot Failed"), Lang(e)))

    @classmethod
    def ActivateHandler(cls, inMessage = None):
        message = FirstValue(inMessage, Lang("Do you want to reboot this server?"))
        DialogueUtils.AuthenticatedOrPasswordUnsetOnly(lambda: Layout.Inst().PushDialogue(QuestionDialogue(
                message, lambda x: cls.RebootReplyHandler(x))))
        
    def Register(self):
        Importer.RegisterNamedPlugIn(
            self,
            'REBOOT', # Key of this plugin for replacement, etc.
            {
                'menuname' : 'MENU_REBOOTSHUTDOWN',
                'menupriority' : 200,
                'menutext' : Lang('Reboot Server'),
                'statusupdatehandler' : XSFeatureReboot.StatusUpdateHandler,
                'activatehandler' : XSFeatureReboot.ActivateHandler
            }
        )

# Register this plugin when module is imported
XSFeatureReboot().Register()
