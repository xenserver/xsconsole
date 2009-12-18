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

class ChangeTimeoutDialogue(InputDialogue):
    def __init__(self):
        self.custom = {
            'title' : Lang("Change Auto-Logout Timeout"),
            'fields' : [ [ Lang("Timeout (minutes)", 20), FirstValue(State.Inst().AuthTimeoutMinutes(), 5), 'timeout', 16 ] ],
            }
        InputDialogue.__init__(self)

    def HandleCommit(self, inValues):
        try:
            timeoutMinutes = int(inValues['timeout'])
        except Exception, e:
            raise Exception("Invalid value - please supply a numeric value")
        
        Auth.Inst().TimeoutSecondsSet(timeoutMinutes * 60)
        return Lang('Timeout Change Successful'), Lang("Timeout changed to ")+inValues['timeout']+Language.Quantity(" minute",  timeoutMinutes)+'.'
        
class XSFeatureChangeTimeout:
    @classmethod
    def StatusUpdateHandler(cls, inPane):
        inPane.AddTitleField(Lang("Change Auto-Logout Time"))
    
        timeout = State.Inst().AuthTimeoutMinutes()
        message = Lang("The current auto-logout time is ") + str(timeout) + " "

        message += Language.Quantity("minute", timeout) + ".  "
        message += Lang("Users will be automatically logged out after there has been no keyboard "
            "activity for this time.  This timeout applies to this console and to "
            "local shells.")
    
        inPane.AddWrappedTextField(message)
        
        inPane.AddKeyHelpField( { Lang("<Enter>") : Lang("Change Timeout") })

    @classmethod
    def ActivateHandler(cls):
        DialogueUtils.AuthenticatedOnly(lambda: Layout.Inst().PushDialogue(ChangeTimeoutDialogue()))
        
    def Register(self):
        Importer.RegisterNamedPlugIn(
            self,
            'CHANGE_TIMEOUT', # Key of this plugin for replacement, etc.
            {
                'menuname' : 'MENU_AUTH',
                'menupriority' : 300,
                'menutext' : Lang('Change Auto-Logout Time') ,
                'statusupdatehandler' : self.StatusUpdateHandler,
                'activatehandler' : self.ActivateHandler
            }
        )

# Register this plugin when module is imported
XSFeatureChangeTimeout().Register()
