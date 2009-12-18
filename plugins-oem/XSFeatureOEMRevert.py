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

class XSFeatureOEMRevert:
    @classmethod
    def StatusUpdateHandler(cls, inPane):
        data = Data.Inst()
        inPane.AddTitleField(Lang("Revert to a Pre-Update Version"))

        inPane.AddWrappedTextField(Lang(
            "Press <Enter> to revert to a version prior to an applied update."))
        inPane.NewLine()
        
        inPane.AddStatusField(Lang('Current Version', 17), data.host.software_version.build_number(''))
        inPane.AddStatusField(Lang('Previous Version', 17), data.backup.alternateversion(''))
            
        inPane.AddKeyHelpField( { Lang("<Enter>") : Lang("Revert") } ) 
 
    @classmethod
    def RevertReplyHandler(cls, inYesNo):
        if inYesNo == 'y':
            try:
                Data.Inst().Revert()
                XSLog('Reverted to previous version')
                Importer.ActivateNamedPlugIn('REBOOT', Lang("To use the reverted version you need to reboot.  Would you like to reboot now?"))
            except Exception, e:
                Layout.Inst().PushDialogue(InfoDialogue( Lang("Revert Failed"), Lang(e)))
                
    @classmethod
    def ActivateHandler(cls):
        DialogueUtils.AuthenticatedOnly(lambda: Layout.Inst().PushDialogue(QuestionDialogue(
                Lang("Do you want to revert this update?  Host and Virtual Machine metadata will revert to the point prior to the update, and Virtual Machines created after the update will be lost.  Changes within Storage Repositories will persist and may not match reverted metadata."), lambda x: cls.RevertReplyHandler(x))))
        
    def Register(self):
        if Data.Inst().CanRevert():
            Importer.RegisterNamedPlugIn(
                self,
                'REVERT', # Key of this plugin for replacement, etc.
                {
                    'menuname' : 'MENU_BUR',
                    'menupriority' : 400,
                    'menutext' : Lang('Revert to a Pre-Update Version') ,
                    'statusupdatehandler' : self.StatusUpdateHandler,
                    'activatehandler' : self.ActivateHandler
                }
            )

# Register this plugin when module is imported
XSFeatureOEMRevert().Register()
