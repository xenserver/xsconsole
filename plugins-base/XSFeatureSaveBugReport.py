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

class SaveBugReportDialogue(FileDialogue):
    def __init__(self):
        self.custom = {
            'title' : Lang("Save Bug Report"),
            'searchregexp' : r'.*',  # Type of bugtool file is .tar
            'deviceprompt' : Lang("Select The Destination Device"), 
            'fileprompt' : Lang("Choose A Destination Filename"),
            'filename' : FileUtils.BugReportFilename(),
            'confirmprompt' : Lang("Press <F8> To Save The Bug Report"),
            'mode' : 'rw'
        }
        FileDialogue.__init__(self) # Must fill in self.custom before calling __init__
        
    def DoAction(self):
        success = False
        
        Layout.Inst().PopDialogue()
        
        Layout.Inst().PushDialogue(BannerDialogue(
            Lang("Saving Bug Report...")))
            
        try:
            try:
                Layout.Inst().Refresh()
                Layout.Inst().DoUpdate()

                filename = self.vdiMount.MountedPath(self.filename)
                FileUtils.AssertSafePath(filename)

                file = open(filename, "w")
                # xen-bugtool requires a value for $USER
                command = "( export USER=root && /usr/sbin/xen-bugtool --yestoall --silent --output=tar --outfd="+str(file.fileno()) + ' )'
                status, output = commands.getstatusoutput(command)
                file.close()

                if status != 0:
                    raise Exception(output)

                Layout.Inst().PopDialogue()
                Layout.Inst().PushDialogue(InfoDialogue(
                    Lang("Saved Bug Report")))

            except Exception, e:
                Layout.Inst().PopDialogue()
                Layout.Inst().PushDialogue(InfoDialogue( Lang("Save Failed"), Lang(e)))
                
        finally:
            try:
                self.PreExitActions()
            except Exception, e:
                Layout.Inst().PushDialogue(InfoDialogue( Lang("Save Failed"), Lang(e)))

class XSFeatureSaveBugReport(PlugIn):
    def __init__(self):
        PlugIn.__init__(self)
        
    @classmethod
    def StatusUpdateHandler(cls, inPane):
        data = Data.Inst()
        inPane.AddTitleField(Lang("Save Bug Report"))

        inPane.AddWrappedTextField(Lang(
            "This option will save a bug report file, containing information about "
            "the state of this machine, to removable media.  This file may contain sensitive data."))
            
        inPane.AddKeyHelpField( { Lang("<Enter>") : Lang("Save Bug Report") } )  
        
    @classmethod
    def ActivateHandler(cls):
        DialogueUtils.AuthenticatedOnly(lambda: Layout.Inst().PushDialogue(QuestionDialogue(
                Lang("This operation may save sensitive data to removable media.  Do you want to continue?"), lambda x: cls.ConfirmHandler(x))))

    @classmethod
    def ConfirmHandler(cls, inYesNo):
        if inYesNo == 'y':
            DialogueUtils.AuthenticatedOnly(lambda: Layout.Inst().PushDialogue(SaveBugReportDialogue()))

    def Register(self):
        data = Data.Inst()
        Importer.RegisterNamedPlugIn(
            self,
            'SAVE_BUG_REPORT', # Key of this plugin for replacement, etc.
            {
                'title' : Lang('Save Bug Report'), # Name of this plugin for plugin list
                'menuname' : 'MENU_TECHNICAL',
                'menupriority' : 300,
                'menutext' : Lang('Save Bug Report') ,
                'statusupdatehandler' : self.StatusUpdateHandler,
                'activatehandler' : self.ActivateHandler
            }
        )

# Register this plugin when module is imported
XSFeatureSaveBugReport().Register()
