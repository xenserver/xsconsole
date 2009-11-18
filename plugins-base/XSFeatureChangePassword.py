# Copyright (c) Citrix Systems 2008. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

if __name__ == "__main__":
    raise Exception("This script is a plugin for xsconsole and cannot run independently")
    
from XSConsoleStandard import *

class ChangePasswordDialogue(Dialogue):
    def __init__(self, inText = None,  inSuccessFunc = None):
        Dialogue.__init__(self)
        self.text = inText
        self.successFunc = inSuccessFunc
        self.isPasswordSet = Auth.Inst().IsPasswordSet()

        pane = self.NewPane(DialoguePane(self.parent))
        pane.TitleSet("Change Password")
        pane.AddBox()
        self.UpdateFields()
        pane.InputIndexSet(None) # Reactivate cursor if this dialogue is initially covered and revealed later
        
    def UpdateFields(self):
        pane = self.Pane()
        pane.ResetFields()
        if self.text is not None:
            pane.AddTitleField(self.text)
        if self.isPasswordSet:
            pane.AddPasswordField(Lang("Old Password", 21), Auth.Inst().DefaultPassword(), 'oldpassword')
        pane.AddPasswordField(Lang("New Password", 21), Auth.Inst().DefaultPassword(), 'newpassword1')
        pane.AddPasswordField(Lang("Repeat New Password", 21), Auth.Inst().DefaultPassword(), 'newpassword2')
        pane.AddKeyHelpField( {
            Lang("<Enter>") : Lang("Next/OK"),
            Lang("<Esc>") : Lang("Cancel"),
            Lang("<Tab>") : Lang("Next")
        })
        
        if pane.InputIndex() is None:
            pane.InputIndexSet(0) # Activate first field for input
        
    def HandleKey(self, inKey):
        handled = True
        pane = self.Pane()
        if inKey == 'KEY_ESCAPE':
            Layout.Inst().PopDialogue()
        elif inKey == 'KEY_ENTER':
            if not pane.IsLastInput():
                pane.ActivateNextInput()
            else:
                inputValues = pane.GetFieldValues()

                Layout.Inst().TransientBanner(Lang("Changing password..."))
                successMessage = Lang('Password Change Successful')
                try:
                    if not Auth.Inst().IsAuthenticated() and self.isPasswordSet:
                        # Log in automatically if we're not
                        Auth.Inst().ProcessLogin('root', inputValues.get('oldpassword', ''))
                        successMessage += Lang(".  User 'root' logged in.")
                        
                    if inputValues['newpassword1'] != inputValues['newpassword2']:
                        raise Exception(Lang('New passwords do not match'))
                    if len(inputValues['newpassword1']) < 6:
                        raise Exception(Lang('New password is too short (minimum length is 6 characters)'))

                    Auth.Inst().ChangePassword(inputValues.get('oldpassword', ''), inputValues['newpassword1'])
                    
                except Exception, e:
                    if self.isPasswordSet:
                        # Only remove the dialogue if this isn't the initial password set (which needs to succeed)
                        Layout.Inst().PopDialogue()
                    else:
                        # Disable the input field so that it gets reactivated by UpdateFields  when the info box is dismissed
                        pane.InputIndexSet(None)
                        
                    Layout.Inst().PushDialogue(InfoDialogue(
                        Lang('Password Change Failed: ')+Lang(e)))
                    
                else:
                    Layout.Inst().PopDialogue()
                    Layout.Inst().PushDialogue(InfoDialogue( successMessage))
                    State.Inst().PasswordChangeRequiredSet(False)
                    
                Data.Inst().Update()

        elif inKey == 'KEY_TAB':
            pane.ActivateNextInput()
        elif inKey == 'KEY_BTAB':
            pane.ActivatePreviousInput()
        elif pane.CurrentInput().HandleKey(inKey):
            pass # Leave handled as True
        else:
            handled = False
        return True

class XSFeatureChangePassword:
    @classmethod
    def StatusUpdateHandler(cls, inPane):
        inPane.AddTitleField(Lang("Change Password"))
    
        inPane.AddWrappedTextField(Lang("Press <Enter> to change the password for user 'root'.  "
        "This will also change the password for local and remote login shells.  "
        "If this host is in a Pool, it will change the password for the Pool."))
        
        inPane.AddKeyHelpField( { Lang("<Enter>") : Lang("Change Password") })
        
    @classmethod
    def ActivateHandler(cls, *inParams):
            DialogueUtils.AuthenticatedOrPasswordUnsetOnly(lambda: Layout.Inst().PushDialogue(ChangePasswordDialogue(*inParams)))
        
    def Register(self):
        Importer.RegisterNamedPlugIn(
            self,
            'CHANGE_PASSWORD', # This key is referred to by name in XSConsoleTerm.py
            {
                'menuname' : 'MENU_AUTH',
                'menupriority' : 200,
                'menutext' : Lang('Change Password') ,
                'statusupdatehandler' : self.StatusUpdateHandler,
                'activatehandler' : self.ActivateHandler
            }
        )

# Register this plugin when module is imported
XSFeatureChangePassword().Register()
