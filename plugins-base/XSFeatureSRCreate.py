# Copyright (c) Citrix Systems 2008. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

if __name__ == "__main__":
    raise Exception("This script is a plugin for xsconsole and cannot run independently")
    
from XSConsoleStandard import *

class SRCreateDialogue(Dialogue):
    srTypeNames = {
        'NFS': Lang('NFS Storage'),
        'ISCSI': Lang('iSCSI Storage'),
        'NETAPP': Lang('NetApp'),
        'CIFS_ISO': Lang('Windows File Sharing (CIFS) ISO Library'),
        'NFS_ISO': Lang('NFS ISO Library')
    }    
    
    def __init__(self):
        Dialogue.__init__(self)
        self.createMenu = Menu()

        choices = ['NFS']
        #choices = ['NFS', 'ISCSI', 'NETAPP', 'CIFS_ISO', 'NFS_ISO']
        for type in choices:
            self.createMenu.AddChoice(name = self.srTypeNames[type],
                onAction = self.HandleCreateChoice,
                handle = type)
                
        
        self.ChangeState('INITIAL')
        
    def BuildPane(self):
        pane = self.NewPane(DialoguePane(self.parent))
        pane.TitleSet(Lang("New Storage Repository"))
        pane.AddBox()
        
    def UpdateFieldsINITIAL(self):
        pane = self.Pane()
        pane.ResetFields()
        pane.AddTitleField(Lang('Please select the type of Storage Repository to create or attach'))
        pane.AddMenuField(self.createMenu)
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
    
    def UpdateFieldsGATHER_NFS(self):
        pane = self.Pane()
        pane.ResetFields()
        pane.AddTitleField(Lang('Please enter a name and path for the new NFS storage'))
        pane.AddInputField(Lang('Name', 16), Lang('NFS Virtual Disk Storage'), 'name')
        pane.AddInputField(Lang('Share Name', 16), 'server:/path', 'sharename')
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
        if pane.CurrentInput() is None:
            pane.InputIndexSet(0)
            
    def UpdateFieldsCONFIRM(self):
        pane = self.Pane()
        pane.ResetFields()
        pane.AddTitleField(Lang('Press <F8> to create this Storage Repository'))
        
        pane.AddStatusField(Lang('SR Type', 16), self.srTypeNames[self.createType])
        for name, value in self.extraInfo:
            pane.AddStatusField(name.ljust(16, ' '), value)
        
        pane.NewLine()


                
        pane.AddKeyHelpField( { Lang("<F8>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
    
    def UpdateFields(self):
        self.Pane().ResetPosition()
        getattr(self, 'UpdateFields'+self.state)() # Despatch method named 'UpdateFields'+self.state

    def ChangeState(self, inState):
        self.state = inState
        self.BuildPane()
        self.UpdateFields()
    
    def HandleKeyINITIAL(self, inKey):
        return self.createMenu.HandleKey(inKey)

    def HandleKeyGATHER_NFS(self, inKey):
        handled = True
        pane = self.Pane()
        if pane.CurrentInput() is None:
            pane.InputIndexSet(0)
        if inKey == 'KEY_ENTER':
            if pane.IsLastInput():
                self.srParams = pane.GetFieldValues()
                self.extraInfo = [
                    (Lang('Name'), self.srParams['name']),
                    (Lang('Share Name'), self.srParams['sharename'])
                    ]
                self.ChangeState('CONFIRM')
            else:
                pane.ActivateNextInput()
        elif inKey == 'KEY_TAB':
            pane.ActivateNextInput()
        elif inKey == 'KEY_BTAB':
            pane.ActivatePreviousInput()
        elif pane.CurrentInput().HandleKey(inKey):
            pass # Leave handled as True
        else:
            handled = False
        return handled

    def HandleKeyCONFIRM(self, inKey):
        handled = False
        if inKey == 'KEY_F(8)':
            self.Commit()
            handled = True
        return handled

    def HandleKey(self,  inKey):
        handled = False
        if hasattr(self, 'HandleKey'+self.state):
            handled = getattr(self, 'HandleKey'+self.state)(inKey)
        
        if not handled and inKey in ('KEY_ESCAPE', 'KEY_LEFT'):
            Layout.Inst().PopDialogue()
            handled = True

        return handled
    
    def HandleCreateChoice(self, inChoice):
        self.createType = inChoice
        
        self.ChangeState('GATHER_'+inChoice)
        
    def Commit(self):
        Layout.Inst().PopDialogue()

        Layout.Inst().TransientBanner(Lang('Creating SR...'))
        try:
            raise Exception(Lang('Not yet implemented'))
            Layout.Inst().PushDialogue(InfoDialogue(Lang("Successful")))

        except Exception, e:
            Layout.Inst().PushDialogue(InfoDialogue(Lang("Failed"), Lang(e)))

class XSFeatureSRCreate:
    @classmethod
    def StatusUpdateHandler(cls, inPane):
        inPane.AddTitleField(Lang("New Storage Repository"))
    
        inPane.AddWrappedTextField(Lang(
            "This option is used to create a new Storage Repository, or attach an ISO library"))
    
    @classmethod
    def ActivateHandler(cls):
        DialogueUtils.AuthenticatedOnly(lambda: Layout.Inst().PushDialogue(SRCreateDialogue()))
    
    def Register(self):
        Importer.RegisterNamedPlugIn(
            self,
            'SR_CREATE', # Key of this plugin for replacement, etc.
            {
                'menuname' : 'MENU_DISK',
                'menupriority' : 50,
                'menutext' : Lang('New Storage Repository') ,
                'statusupdatehandler' : self.StatusUpdateHandler,
                'activatehandler' : self.ActivateHandler
            }
        )

# Register this plugin when module is imported
XSFeatureSRCreate().Register()
