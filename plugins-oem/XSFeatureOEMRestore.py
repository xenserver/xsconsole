# Copyright (c) Citrix Systems 2008. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

if __name__ == "__main__":
    raise Exception("This script is a plugin for xsconsole and cannot run independently")
    
from XSConsoleStandard import *

class OEMRestoreDialogue(FileDialogue):
    def __init__(self):

        self.custom = {
            'title' : Lang("Restore Server State"),
            'searchregexp' : r'.*\.xbk$',  # Type of backup file is .xbk
            'deviceprompt' : Lang("Select the device containing the backup file"), 
            'fileprompt' : Lang("Select the Backup File"),
            'confirmprompt' : Lang("Press <F8> to Begin the Restore Process"),
            'mode' : 'ro'
        }
        FileDialogue.__init__(self) # Must fill in self.custom before calling __init__
        
    def DoAction(self):
        success = False
        
        Layout.Inst().PopDialogue()
        
        Layout.Inst().PushDialogue(BannerDialogue(
            Lang("Restoring from backup... This may take several minutes.")))
            
        hostEnabled = Data.Inst().host.enabled(False)
        
        try:
            try:
                Layout.Inst().Refresh()
                Layout.Inst().DoUpdate()
                
                if len(HotAccessor().local_host.resident_VMs([])) > 1: # Count includes dom0
                    raise Exception(Lang("One or more Virtual Machines are running on this host.  Please migrate, shut down or suspend Virtual Machines before continuing."))

                Data.Inst().LocalHostDisable()
                
                hostRef = Data.Inst().host.uuid(None)
                if hostRef is None:
                    raise Exception("Internal error 1")
                    
                filename = self.vdiMount.MountedPath(self.filename)
                FileUtils.AssertSafePath(filename)
                command = "/opt/xensource/bin/xe host-restore file-name='"+filename+"' host="+hostRef
                status, output = commands.getstatusoutput(command)
                
                if status != 0:
                    raise Exception(output)
                
                Layout.Inst().PopDialogue()
                Layout.Inst().PushDialogue(InfoDialogue(
                    Lang("Restore Successful"), Lang("Please reboot to use the restored state.")))
                XSLog('Restore successful')
                hostEnabled = False

            except Exception, e:
                Layout.Inst().PopDialogue()
                Layout.Inst().PushDialogue(InfoDialogue( Lang("Restore Failed"), Lang(e)))
                
        finally:
            try:
                self.PreExitActions()
                if hostEnabled:
                    # Dont leave the host disabled if restoration has failed
                    Data.Inst().LocalHostEnable()
            except Exception, e:
                Layout.Inst().PushDialogue(InfoDialogue( Lang("Restore Failed"), Lang(e)))


class XSFeatureOEMRestore:
    @classmethod
    def StatusUpdateHandler(cls, inPane):
        data = Data.Inst()
        inPane.AddTitleField(Lang("Restore Server State"))

        inPane.AddWrappedTextField(Lang(
            "Press <Enter> to restore the server state from removable media."))
        inPane.AddKeyHelpField( { Lang("<Enter>") : Lang("Restore") } ) 
 
    @classmethod
    def ActivateHandler(cls):
        DialogueUtils.AuthenticatedOnly(lambda: Layout.Inst().PushDialogue(OEMRestoreDialogue()))
        
    def Register(self):
        Importer.RegisterNamedPlugIn(
            self,
            'RESTORE', # Key of this plugin for replacement, etc.
            {
                'menuname' : 'MENU_BUR',
                'menupriority' : 300,
                'menutext' : Lang('Restore Server State from Backup') ,
                'statusupdatehandler' : self.StatusUpdateHandler,
                'activatehandler' : self.ActivateHandler
            }
        )

# Register this plugin when module is imported
XSFeatureOEMRestore().Register()
