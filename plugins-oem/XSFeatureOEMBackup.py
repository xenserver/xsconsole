# Copyright (c) Citrix Systems 2008. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

if __name__ == "__main__":
    raise Exception("This script is a plugin for xsconsole and cannot run independently")
    
from XSConsoleStandard import *
from XSConsolePlugIn import *

class OEMBackupDialogue(FileDialogue):
    def __init__(self):

        self.custom = {
            'title' : Lang("Backup Server State"),
            'searchregexp' : r'.*\.xbk$',  # Type of backup file is .xbk
            'deviceprompt' : Lang("Select the backup device"), 
            'fileprompt' : Lang("Choose the backup filename"),
            'filename' : 'backup.xbk',
            'confirmprompt' : Lang("Press <F8> to begin the backup process"),
            'mode' : 'rw'
        }
        FileDialogue.__init__(self) # Must fill in self.custom before calling __init__
        
    def DoAction(self):
        filename = self.vdiMount.MountedPath(self.filename)
        if os.path.isfile(filename):
            Layout.Inst().PushDialogue(QuestionDialogue(
                Lang("File already exists.  Do you want to overwrite it?"), lambda x: self.DoOverwriteChoice(x)))
        else:
            self.DoCommit()
    
    def DoOverwriteChoice(self, inChoice):
        if inChoice == 'y':
            filename = self.vdiMount.MountedPath(self.filename)
            os.remove(filename)
            self.DoCommit()
        else:
            self.ChangeState('FILES')
    
    def DoCommit(self):
        success = False
        
        Layout.Inst().PopDialogue()
        
        Layout.Inst().PushDialogue(BannerDialogue(
            Lang("Saving to backup... This make take several minutes.  Press <Ctrl-C> to abort.")))
            
        try:
            try:
                Layout.Inst().Refresh()
                Layout.Inst().DoUpdate()
                
                hostRef = Data.Inst().host.uuid(None)
                if hostRef is None:
                    raise Exception("Internal error 1")
                    
                filename = self.vdiMount.MountedPath(self.filename)
                FileUtils.AssertSafePath(filename)
                command = "/opt/xensource/bin/xe host-backup file-name='"+filename+"' host="+hostRef
                status, output = commands.getstatusoutput(command)
                
                if status != 0:
                    raise Exception(output)
                
                Layout.Inst().PopDialogue()
                Layout.Inst().PushDialogue(InfoDialogue(
                    Lang("Backup Successful")))

            except Exception, e:
                Layout.Inst().PopDialogue()
                Layout.Inst().PushDialogue(InfoDialogue( Lang("Backup Failed"), Lang(e)))
                
        finally:
            try:
                self.PreExitActions()
            except Exception, e:
                Layout.Inst().PushDialogue(InfoDialogue( Lang("Backup Failed"), Lang(e)))


class XSFeatureOEMBackup(PlugIn):
    def __init__(self):
        PlugIn.__init__(self)
        
    @classmethod
    def StatusUpdateHandler(cls, inPane):
        data = Data.Inst()
        inPane.AddTitleField(Lang("Backup Server State"))

        inPane.AddWrappedTextField(Lang(
            "Press <Enter> to backup the server state to removable media."))
            
        inPane.AddKeyHelpField( { Lang("<Enter>") : Lang("Backup") } ) 
        
    @classmethod
    def ActivateHandler(cls):
        DialogueUtils.AuthenticatedOnly(lambda: Layout.Inst().PushDialogue(OEMBackupDialogue()))
        
    def Register(self):
        data = Data.Inst()
        Importer.RegisterNamedPlugIn(
            self,
            'BACKUP', # Key of this plugin for replacement, etc.
            {
                'title' : Lang('Backup Server State'), # Name of this plugin for plugin list
                'menuname' : 'MENU_BUR',
                'menupriority' : 200,
                'menutext' : Lang('Backup Server State') ,
                'statusupdatehandler' : self.StatusUpdateHandler,
                'activatehandler' : self.ActivateHandler
            }
        )

# Register this plugin when module is imported
XSFeatureOEMBackup().Register()
