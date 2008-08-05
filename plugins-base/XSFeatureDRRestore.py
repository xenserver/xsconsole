# Copyright (c) Citrix Systems 2008. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

if __name__ == "__main__":
    raise Exception("This script is a plugin for xsconsole and cannot run independently")
    
from XSConsoleStandard import *

class DRRestoreSelection(Dialogue):

    def __init__(self, date_choices, vdi_uuid, sr_uuid):
        Dialogue.__init__(self)
    
        choices = []
        self.vdi_uuid = vdi_uuid
        self.sr_uuid = sr_uuid
        self.date_choices = date_choices.splitlines()
        index = 0
        for choice in self.date_choices:
            cdef = ChoiceDef(choice, lambda i=index: self.HandleTestChoice(i))
            index = index + 1
            choices.append(cdef)

        self.testMenu = Menu(self, None, "", choices)

        self.methodMenu = Menu(self, None, "", [
           ChoiceDef("Only VMs on This SR", lambda: self.HandleMethodChoice('sr', False)),
           ChoiceDef("All VM Metadata", lambda: self.HandleMethodChoice('all', False)),
           ChoiceDef("Only VMs on This SR (Dry Run)", lambda: self.HandleMethodChoice('sr', True)),
           ChoiceDef("All VM Metadata (Dry Run)", lambda: self.HandleMethodChoice('all', True)),
        ])
        self.ChangeState('LISTDATES')
    
    def BuildPane(self):
        pane = self.NewPane(DialoguePane(self.parent))
        pane.TitleSet(Lang('Restore Virtual Machine Metadata'))
        pane.AddBox()
    
    def UpdateFieldsLISTDATES(self):
        pane = self.Pane()
        pane.ResetFields()
        
        pane.TitleSet("Available Metadata Backups")
        pane.AddTitleField(Lang("Select Metadata Backup to Restore From"))
        pane.AddMenuField(self.testMenu)
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
       
    def UpdateFieldsCHOOSERESTORE(self):
        pane = self.Pane()
        pane.ResetFields()

        pane.TitleSet("Restore Backup from " + self.chosen_date)
        pane.AddTitleField("Select the set of VMs to restore from " + self.chosen_date)
        pane.AddMenuField(self.methodMenu)
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("Restore VMs"), Lang("<Esc>") : Lang("Cancel") } )

    def UpdateFields(self):
        self.Pane().ResetPosition()
        getattr(self, 'UpdateFields'+self.state)() # Despatch method named 'UpdateFields'+self.state

    def ChangeState(self, inState):
        self.state = inState
        self.BuildPane()
        self.UpdateFields()

    def HandleTestChoice(self,  inChoice):
        self.chosen_date = self.date_choices[inChoice]
        self.ChangeState('CHOOSERESTORE')

    def HandleMethodChoice(self, inChoice, dryRun):
        if inChoice != 'sr' and inChoice != 'all':
            Layout.Inst().PopDialogue()
            Layout.Inst().PushDialogue(InfoDialogue(Lang("Internal Error, unexpected choice: " + inChoice)))
        else:
            chosen_mode = inChoice
            if dryRun:
              dry_flag="-n "
            else:
              dry_flag=""
            Layout.Inst().TransientBanner(Lang("Restoring VM Metadata.  This may take a few minutes..."))
            command = "/opt/xensource/bin/xe-restore-metadata -y " + dry_flag +" -u " + self.sr_uuid + " -x " + self.vdi_uuid + " -d " + self.chosen_date + " -m " + chosen_mode
            status, output = commands.getstatusoutput(command)
            status = os.WEXITSTATUS(status)
            Layout.Inst().PopDialogue()
            if status == 0:
                Layout.Inst().PushDialogue(InfoDialogue(Lang("Metadata Restore Succeeded: ") + output))
            else:
                Layout.Inst().PushDialogue(InfoDialogue(Lang("Metadata Restore Failed: ") + output))

    def HandleKey(self, inKey):
        handled = False
        if hasattr(self, 'HandleKey'+self.state):
            handled = getattr(self, 'HandleKey'+self.state)(inKey)

        if not handled and inKey == 'KEY_ESCAPE':
            Layout.Inst().PopDialogue()
            handled = True

        return handled
 
    def HandleKeyLISTDATES(self, inKey):
        handled = self.testMenu.HandleKey(inKey)
        if not handled and inKey == 'KEY_LEFT':
            Layout.Inst().PopDialogue()
            handled = True
        return handled

    def HandleKeyCHOOSERESTORE(self, inKey):
        handled = self.methodMenu.HandleKey(inKey)
        if not handled and inKey == 'KEY_LEFT':
            Layout.Inst().PopDialogue()
            handled = True
        return handled

class DRRestoreDialogue(SRDialogue):
    def __init__(self):

        self.custom = {
            'title' : Lang("Select Storage Repository to Restore From"),
            'prompt' : Lang("Please select a Storage Repository"),
            'mode' : 'rw',
            'capabilities' : 'vdi_create'
        }
        SRDialogue.__init__(self) # Must fill in self.custom before calling __init__

    def DoAction(self, inSR):
        Layout.Inst().PopDialogue()
        Layout.Inst().TransientBanner(Lang("Searching for backup VDI...\n\nCtrl-C to abort"))
        sr_uuid = inSR['uuid']
        try:
            # probe for the restore VDI UUID
            command = "/opt/xensource/bin/xe-restore-metadata -p -u " + sr_uuid
            status, output = commands.getstatusoutput(command)
            status = os.WEXITSTATUS(status)
            if status != 0:
                raise Exception(output)
            vdi_uuid = output

            # list the available backups
            Layout.Inst().TransientBanner(Lang("Found VDI, retrieving available backups..."))
            command = "/opt/xensource/bin/xe-restore-metadata -l -u " + sr_uuid + " -x " + vdi_uuid
            status, output = commands.getstatusoutput(command)
            status = os.WEXITSTATUS(status)
            if status != 0:
                raise Exception(output)
            Layout.Inst().PushDialogue(DRRestoreSelection(output, vdi_uuid, sr_uuid))
        except Exception, e:
            Layout.Inst().PushDialogue(InfoDialogue( Lang("Metadata Restore failed: ")+str(e)))
        Data.Inst().Update()

class XSFeatureDRRestore:
    @classmethod
    def StatusUpdateHandler(cls, inPane):
        data = Data.Inst()
        inPane.AddTitleField(Lang("Restore Virtual Machine Metadata"))

        inPane.AddWrappedTextField(Lang(
            "Press <Enter> to restore Virtual Machine metadata from a Storage Repository."))  
        inPane.AddKeyHelpField( { Lang("<Enter>") : Lang("Backup") } )  
        
    @classmethod
    def ActivateHandler(cls):
        DialogueUtils.AuthenticatedOnly(lambda: Layout.Inst().PushDialogue(DRRestoreDialogue()))
        
    def Register(self):
        Importer.RegisterNamedPlugIn(
            self,
            'DRRESTORE', # Key of this plugin for replacement, etc.
            {
                'menuname' : 'MENU_BUR',
                'menupriority' : 90,
                'menutext' : Lang('Restore Virtual Machine Metadata') ,
                'statusupdatehandler' : self.StatusUpdateHandler,
                'activatehandler' : self.ActivateHandler
            }
        )

# Register this plugin when module is imported
XSFeatureDRRestore().Register()
