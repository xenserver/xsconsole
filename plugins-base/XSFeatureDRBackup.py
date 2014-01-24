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

class DRBackupDialogue(SRDialogue):
    def __init__(self):

        self.custom = {
            'title' : Lang("Select Storage Repository for Backup"),
            'prompt' : Lang("Please select a Storage Repository"),
            'mode' : 'rw',
            'capabilities' : 'vdi_create'
        }
        SRDialogue.__init__(self) # Must fill in self.custom before calling __init__

    def DoAction(self, inSR):
        Layout.Inst().PopDialogue()
        try:
            # determine if there is a backup VDI or not, and if not just create one
            sr_uuid = inSR['uuid']
            command = "%s/xe-backup-metadata -n -u %s" % (Config.Inst().HelperPath(), sr_uuid)
            
            status, output = commands.getstatusoutput(command)
            status = os.WEXITSTATUS(status)
            initalize_vdi = ""
            if status == 3:
               initalize_vdi = "-c"
            elif status != 0 and status != 3:
               raise Exception(output)

            Layout.Inst().TransientBanner(Lang("Backing up metadata... This may take several minutes."))
            command = "%s/xe-backup-metadata %s -u %s" % (Config.Inst().HelperPath(), initalize_vdi, sr_uuid)
            status, output = commands.getstatusoutput(command)
            if status == 0:
                Layout.Inst().PushDialogue(InfoDialogue(Lang("Backup Successful"), output))
            else:
                raise Exception(output)
        except Exception, e:
            Layout.Inst().PushDialogue(InfoDialogue(Lang("Metadata Backup failed: ")+Lang(e)))
        Data.Inst().Update()

class XSFeatureDRBackup:
    @classmethod
    def StatusUpdateHandler(cls, inPane):
        data = Data.Inst()
        inPane.AddTitleField(Lang("Backup Virtual Machine Metadata"))

        inPane.AddWrappedTextField(Lang(
            "Press <Enter> to backup Virtual Machine metadata to a Storage Repository.  This will back up the information associated with the VM configuration to a special backup disk on the Storage Repository.  You can subsequently restore this metadata if you migrate the Storage Repository to another XenServer pool."))
        inPane.AddKeyHelpField( { Lang("<Enter>") : Lang("Backup") } )  
        
    @classmethod
    def ActivateHandler(cls):
        DialogueUtils.AuthenticatedOnly(lambda: Layout.Inst().PushDialogue(DRBackupDialogue()))
        
    def Register(self):
        Importer.RegisterNamedPlugIn(
            self,
            'DRBACKUP', # Key of this plugin for replacement, etc.
            {
                'menuname' : 'MENU_BUR',
                'menupriority' : 80,
                'menutext' : Lang('Backup Virtual Machine Metadata') ,
                'statusupdatehandler' : self.StatusUpdateHandler,
                'activatehandler' : self.ActivateHandler
            }
        )

# Register this plugin when module is imported
XSFeatureDRBackup().Register()
