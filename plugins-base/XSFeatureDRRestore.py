# Copyright (c) Citrix Systems 2008. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

if __name__ == "__main__":
    raise Exception("This script is a plugin for xsconsole and cannot run independently")
    
from XSConsoleStandard import *

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
        Layout.Inst().TransientBanner(Lang("Searching for backup VDI..."))
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

            Layout.Inst().PushDialogue(InfoDialogue(output))
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
        # DialogueUtils.AuthenticatedOnly(lambda: Layout.Inst().PushDialogue(DRRestoreDialogue()))
        Layout.Inst().PushDialogue(DRRestoreDialogue())
        
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
