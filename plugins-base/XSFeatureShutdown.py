# Copyright (c) Citrix Systems 2008. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

if __name__ == "__main__":
    raise Exception("This script is a plugin for xsconsole and cannot run independently")
    
from XSConsoleStandard import *

class XSFeatureShutdown:
    @classmethod
    def StatusUpdateHandler(cls, inPane):
        inPane.AddTitleField(Lang("Shutdown Server"))
    
        inPane.AddWrappedTextField(Lang(
            "Press <Enter> to shutdown this server."))
    
        inPane.AddKeyHelpField( {
            Lang("<Enter>") : Lang("Shutdown Server")
        } )

    @classmethod
    def ShutdownReplyHandler(cls,  inYesNo):
        if inYesNo == 'y':
            try:
                Layout.Inst().ExitBannerSet(Lang("Shutting Down..."))
                Layout.Inst().ExitCommandSet('/sbin/shutdown -h now')
            except Exception, e:
                Layout.Inst().PushDialogue(InfoDialogue(Lang("Shutdown Failed"), Lang(e)))

    @classmethod
    def ActivateHandler(cls):
        DialogueUtils.AuthenticatedOrPasswordUnsetOnly(lambda: Layout.Inst().PushDialogue(QuestionDialogue(
                Lang("Do you want to shutdown this server?"), lambda x: cls.ShutdownReplyHandler(x))))
        
    def Register(self):
        Importer.RegisterNamedPlugIn(
            self,
            'SHUTDOWN', # Key of this plugin for replacement, etc.
            {
                'menuname' : 'MENU_REBOOTSHUTDOWN',
                'menupriority' : 200,
                'menutext' : Lang('Shutdown Server'),
                'statusupdatehandler' : XSFeatureShutdown.StatusUpdateHandler,
                'activatehandler' : XSFeatureShutdown.ActivateHandler
            }
        )

# Register this plugin when module is imported
XSFeatureShutdown().Register()
