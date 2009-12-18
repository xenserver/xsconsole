# Copyright (c) 2008-2009 Citrix Systems Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 only.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

if __name__ == "__main__":
    raise Exception("This script is a plugin for xsconsole and cannot run independently")
    
from XSConsoleStandard import *

class SaveBugReportDialogue(FileDialogue):
    def __init__(self):
        self.custom = {
            'title' : Lang("Save Bug Report"),
            'searchregexp' : r'.*',  # Type of bugtool file is .tar
            'deviceprompt' : Lang("Select the Destination Device"), 
            'fileprompt' : Lang("Choose a Destination Filename"),
            'filename' : FileUtils.BugReportFilename(),
            'confirmprompt' : Lang("Press <F8> to Save the Bug Report"),
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

class XSFeatureSaveBugReport:
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
        Importer.RegisterNamedPlugIn(
            self,
            'SAVE_BUG_REPORT', # Key of this plugin for replacement, etc.
            {
                'menuname' : 'MENU_TECHNICAL',
                'menupriority' : 300,
                'menutext' : Lang('Save Bug Report') ,
                'statusupdatehandler' : self.StatusUpdateHandler,
                'activatehandler' : self.ActivateHandler
            }
        )

# Register this plugin when module is imported
XSFeatureSaveBugReport().Register()
