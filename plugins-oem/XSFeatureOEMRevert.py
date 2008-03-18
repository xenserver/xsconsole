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
        
        inPane.AddStatusField(Lang('Current Label', 16), data.backup.currentlabel(''))
        inPane.AddStatusField(Lang('Previous Label', 16), data.backup.previouslabel(''))
            
        inPane.AddKeyHelpField( { Lang("<Enter>") : Lang("Revert") } ) 
 
    @classmethod
    def RevertReplyHandler(cls, inYesNo):
        if inYesNo == 'y':
            try:
                Data.Inst().Revert()
                Importer.ActivateNamedPlugIn('REBOOT', Lang("To use the reverted version you need to reboot.  Would you like to reboot now?"))
            except Exception, e:
                Layout.Inst().PushDialogue(InfoDialogue( Lang("Revert Failed"), Lang(e)))
                
    @classmethod
    def ActivateHandler(cls):
        DialogueUtils.AuthenticatedOnly(lambda: Layout.Inst().PushDialogue(QuestionDialogue(
                Lang("Do you want to revert this upgrade?"), lambda x: cls.RevertReplyHandler(x))))
        
    def Register(self):
        if Data.Inst().backup.canrevert(False):
            Importer.RegisterNamedPlugIn(
                self,
                'REVERT', # Key of this plugin for replacement, etc.
                {
                    'menuname' : 'MENU_BUR',
                    'menupriority' : 400,
                    'menutext' : Lang('Revert Server State From Backup') ,
                    'statusupdatehandler' : self.StatusUpdateHandler,
                    'activatehandler' : self.ActivateHandler
                }
            )

# Register this plugin when module is imported
XSFeatureOEMRevert().Register()
