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

class UploadBugReportDialogue(InputDialogue):
    def __init__(self):
        self.custom = {
            'title' : Lang("Upload Bug Report"),
            'info' : Lang("Please enter the destination server name, and proxy name if required (blank for none).  Use the form ftp://username:password@server:port for authenticated servers and proxies."), 
            'fields' : [
                [Lang("Destination", 14), Config.Inst().FTPServer(), 'destination'],
                [Lang("Filename", 14), FileUtils.BugReportFilename(), 'filename'],
                [Lang("Proxy", 14), '', 'proxy']
            ]
        }
        InputDialogue.__init__(self)

    def HandleCommit(self, inValues):
        Layout.Inst().TransientBanner(Lang("Uploading Bug Report..."))
            
        hostRef = ShellUtils.MakeSafeParam(Data.Inst().host.uuid(''))
        destServer = ShellUtils.MakeSafeParam(inValues['destination'])
        if not re.match(r'(ftp|http|https)://', destServer):
            raise Exception(Lang('Destination name must start with ftp://, http:// or https://'))
        destFilename = ShellUtils.MakeSafeParam(inValues['filename'])
        destURL = destServer.rstrip('/')+'/'+destFilename.lstrip('/')
        proxy = ShellUtils.MakeSafeParam(inValues['proxy'])
        
        command = "/opt/xensource/bin/xe host-bugreport-upload host='"+hostRef+"' url='"+destURL+"'"
        if proxy != '':
            command += " http_proxy='"+proxy+"'"
            
        status, output = commands.getstatusoutput(command)
                
        if status != 0:
            XSLogError('Upload bugreport failed', output) # Error output can be verbose, so syslog only
            raise Exception(Lang('The bug report upload failed.  Please check that the destination directory is correct, and that the server accepts anonymous uploads to that directory and is reachable from this network.')) 

        return (Lang("Bug Report Uploaded Successfully"), None)
        

class XSFeatureUploadBugReport:
    @classmethod
    def StatusUpdateHandler(cls, inPane):
        data = Data.Inst()
        inPane.AddTitleField(Lang("Upload Bug Report"))

        inPane.AddWrappedTextField(Lang(
            "This option will upload a bug report file, containing information about "
            "the state of this machine to the support ftp server.  This file may contain sensitive data."))
            
        inPane.AddKeyHelpField( { Lang("<Enter>") : Lang("Upload Bug Report") } )  

    @classmethod
    def ActivateHandler(cls):
        DialogueUtils.AuthenticatedOnly(lambda: Layout.Inst().PushDialogue(QuestionDialogue(
                Lang("This operation may upload sensitive data to the support server.  Do you want to continue?"), lambda x: cls.ConfirmHandler(x))))

    @classmethod
    def ConfirmHandler(cls, inYesNo):
        if inYesNo == 'y':
            DialogueUtils.AuthenticatedOnly(lambda: Layout.Inst().PushDialogue(UploadBugReportDialogue()))

    def Register(self):
        Importer.RegisterNamedPlugIn(
            self,
            'UPLOAD_BUG_REPORT', # Key of this plugin for replacement, etc.
            {
                'menuname' : 'MENU_TECHNICAL',
                'menupriority' : 200,
                'menutext' : Lang('Upload Bug Report') ,
                'statusupdatehandler' : self.StatusUpdateHandler,
                'activatehandler' : self.ActivateHandler
            }
        )

# Register this plugin when module is imported
XSFeatureUploadBugReport().Register()
