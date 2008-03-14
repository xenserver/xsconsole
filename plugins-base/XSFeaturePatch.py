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

class PatchDialogue(FileDialogue):
    def __init__(self):

        self.custom = {
            'title' : Lang("Apply Software Upgrade"),
            'searchregexp' : r'.*\.xbk$',  # Type of backup file is .xbk
            'deviceprompt' : Lang("Select the device containing the upgrade"), 
            'fileprompt' : Lang("Select the upgrade file"),
            'confirmprompt' : Lang("Press <F8> to begin the upgrade process"),
            'mode' : 'ro'
        }
        FileDialogue.__init__(self) # Must fill in self.custom before calling __init__
        
    def DoAction(self):
        success = False
        
        Layout.Inst().PopDialogue()
        
        Layout.Inst().PushDialogue(BannerDialogue(
            Lang("Applying upgrade... This make take several minutes.  Press <Ctrl-C> to abort.")))
            
        try:
            try:
                Layout.Inst().Refresh()
                Layout.Inst().DoUpdate()
                
                hostRef = Data.Inst().host.uuid(None)
                if hostRef is None:
                    raise Exception("Internal error 1")
                    
                filename = self.vdiMount.MountedPath(self.filename)
                FileUtils.AssertSafePath(filename)
                command = "/opt/xensource/bin/xe update-upload file-name='"+filename+"' host-uuid="+hostRef
                status, output = commands.getstatusoutput(command)
                
                if status != 0:
                    raise Exception(output)
                
                Layout.Inst().PopDialogue()
                Layout.Inst().PushDialogue(InfoDialogue(
                    Lang("Upgrade Successful"), Lang("Please reboot to use the newly installed software.")))

            except Exception, e:
                Layout.Inst().PopDialogue()
                Layout.Inst().PushDialogue(InfoDialogue( Lang("Software Upgrade Failed"), Lang(e)))
                
        finally:
            try:
                self.PreExitActions()
            except Exception, e:
                Layout.Inst().PushDialogue(InfoDialogue( Lang("Software Upgrade Failed"), Lang(e)))

class XSFeaturePatch(PlugIn):
    def __init__(self):
        PlugIn.__init__(self)
        
    @classmethod
    def StatusUpdateHandler(cls, inPane):
        data = Data.Inst()
        inPane.AddTitleField(Lang("Apply Upgrade"))

        inPane.AddWrappedTextField(Lang(
            "Press <Enter> to apply a software upgrade."))
        inPane.AddKeyHelpField( { Lang("<Enter>") : Lang("Upgrade") } )  
        
    @classmethod
    def ActivateHandler(cls):
        DialogueUtils.AuthenticatedOnly(lambda: Layout.Inst().PushDialogue(PatchDialogue()))
        
    def Register(self):
        data = Data.Inst()
        Importer.RegisterNamedPlugIn(
            self,
            'PATCH', # Key of this plugin for replacement, etc.
            {
                'title' : Lang('Apply Update'), # Name of this plugin for plugin list
                'menuname' : 'MENU_BUR',
                'menupriority' : 100,
                'menutext' : Lang('Apply Update') ,
                'statusupdatehandler' : self.StatusUpdateHandler,
                'activatehandler' : self.ActivateHandler
            }
        )

# Register this plugin when module is imported
XSFeaturePatch().Register()
