# Copyright (c) Citrix Systems 2008. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

if __name__ == "__main__":
    raise Exception("This script is a plugin for xsconsole and cannot run independently")
    
from XSConsoleStandard import *

class ResetDialogue(Dialogue):
    def __init__(self):
        Dialogue.__init__(self)

        self.ChangeState('INITIAL')
        
    def BuildPaneBase(self):
        pane = self.NewPane(DialoguePane(self.parent))
        pane.TitleSet(Lang("Reset to Factory Defaults"))
        pane.AddBox()
    
    def BuildPaneINITIAL(self):
        self.BuildPaneBase()
        self.UpdateFields()

    def BuildPaneCONFIRM(self):
        self.BuildPaneBase()
        self.UpdateFields()
    
    def ChangeState(self, inState):
        self.state = inState
        getattr(self, 'BuildPane'+self.state)() # Despatch method named 'BuildPane'+self.state
    
    def UpdateFields(self):
        self.Pane().ResetPosition()
        getattr(self, 'UpdateFields'+self.state)() # Despatch method named 'UpdateFields'+self.state
        
    def UpdateFieldsINITIAL(self):
        pane = self.Pane()
        pane.ResetFields()
        
        pane.AddWarningField(Lang("WARNING"))
        pane.AddWrappedTextField(Lang("This function will delete ALL configuration information, ALL virtual machines "
            "and ALL information within Storage Repositories on local disks.  "
            "This operation cannot be undone.  Do you want to continue?"))
        pane.AddKeyHelpField( { Lang("<F8>") : Lang("Continue"), Lang("<Esc>") : Lang("Cancel") } )

    def UpdateFieldsCONFIRM(self):
        pane = self.Pane()
        pane.ResetFields()
        
        pane.AddWrappedBoldTextField(Lang("Press <Enter> to confirm that you want to reset configuration data and "
            "erase all information in Storage Repositories on local disks.  "
            "The data cannot be recovered after this step."))

        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("Reset to Factory Defaults"), Lang("<Esc>") : Lang("Cancel") } )

    def HandleKey(self, inKey):
        handled = False
        if hasattr(self, 'HandleKey'+self.state):
            handled = getattr(self, 'HandleKey'+self.state)(inKey)
        
        if not handled and inKey == 'KEY_ESCAPE':
            Layout.Inst().PopDialogue()
            handled = True

        return handled
        
    def HandleKeyINITIAL(self, inKey):
        handled = False
        
        if inKey == 'KEY_F(8)':
            self.ChangeState('CONFIRM')
            handled = True
            
        return handled
        
    def HandleKeyCONFIRM(self, inKey):
        handled = False
        
        if inKey == 'KEY_ENTER':
            self.DoAction()
            handled = True
            
        return handled

    def DoAction(self):
        Layout.Inst().ExitBannerSet(Lang("Resetting..."))
        Layout.Inst().SubshellCommandSet("/opt/xensource/libexec/revert-to-factory yesimeanit && sleep 2")
        Data.Inst().SetVerboseBoot(False)
        State.Inst().RebootMessageSet(Lang("This server must reboot to complete the reset process.  Reboot the server now?"))


class XSFeatureReset:
    @classmethod
    def StatusUpdateHandler(cls, inPane):
        data = Data.Inst()
        inPane.AddTitleField(Lang("Reset to Factory Defaults"))

        inPane.AddWrappedTextField(Lang(
            "This option will reset all configuration information to default values, "
            "delete all virtual machines and delete all Storage Repositories on local disks."))
            
        inPane.AddKeyHelpField( { Lang("<Enter>") : Lang("Reset") } )  

    @classmethod
    def ActivateHandler(cls):
        DialogueUtils.AuthenticatedOnly(lambda: Layout.Inst().PushDialogue(ResetDialogue()))
        
    def Register(self):
        Importer.RegisterNamedPlugIn(
            self,
            'RESET', # Key of this plugin for replacement, etc.
            {
                'menuname' : 'MENU_TECHNICAL',
                'menupriority' : 500,
                'menutext' : Lang('Reset To Factory Defaults') ,
                'statusupdatehandler' : self.StatusUpdateHandler,
                'activatehandler' : self.ActivateHandler
            }
        )

# Register this plugin when module is imported
XSFeatureReset().Register()
