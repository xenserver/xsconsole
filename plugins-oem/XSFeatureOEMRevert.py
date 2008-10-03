# Copyright (c) Citrix Systems 2008. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

if __name__ == "__main__":
    raise Exception("This script is a plugin for xsconsole and cannot run independently")
    
from XSConsoleStandard import *

class XSFeatureOEMRevert:
    @classmethod
    def StatusUpdateHandler(cls, inPane):
        data = Data.Inst()
        inPane.AddTitleField(Lang("Revert to a Pre-Update Version"))

        inPane.AddWrappedTextField(Lang(
            "Press <Enter> to revert to a version prior to an applied update."))
        inPane.NewLine()
        
        inPane.AddStatusField(Lang('Current Version', 17), data.host.software_version.build_number(''))
        inPane.AddStatusField(Lang('Previous Version', 17), data.backup.alternateversion(''))
            
        inPane.AddKeyHelpField( { Lang("<Enter>") : Lang("Revert") } ) 
 
    @classmethod
    def RevertReplyHandler(cls, inYesNo):
        if inYesNo == 'y':
            try:
                Data.Inst().Revert()
                XSLog('Reverted to previous version')
                Importer.ActivateNamedPlugIn('REBOOT', Lang("To use the reverted version you need to reboot.  Would you like to reboot now?"))
            except Exception, e:
                Layout.Inst().PushDialogue(InfoDialogue( Lang("Revert Failed"), Lang(e)))
                
    @classmethod
    def ActivateHandler(cls):
        DialogueUtils.AuthenticatedOnly(lambda: Layout.Inst().PushDialogue(QuestionDialogue(
                Lang("Do you want to revert this update?  Host and Virtual Machine metadata will revert to the point prior to the update, and Virtual Machines created after the update will be lost.  Changes within Storage Repositories will persist and may not match reverted metadata."), lambda x: cls.RevertReplyHandler(x))))
        
    def Register(self):
        if Data.Inst().CanRevert():
            Importer.RegisterNamedPlugIn(
                self,
                'REVERT', # Key of this plugin for replacement, etc.
                {
                    'menuname' : 'MENU_BUR',
                    'menupriority' : 400,
                    'menutext' : Lang('Revert to a Pre-Update Version') ,
                    'statusupdatehandler' : self.StatusUpdateHandler,
                    'activatehandler' : self.ActivateHandler
                }
            )

# Register this plugin when module is imported
XSFeatureOEMRevert().Register()
