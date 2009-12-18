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

class XSFeatureLogInOut:
    @classmethod
    def StatusUpdateHandler(cls, inPane):
        if Auth.Inst().IsAuthenticated():
            inPane.AddTitleField(Lang("Log Out"))
            inPane.AddWrappedTextField(Lang("Press <Enter> to log out."))
            inPane.AddKeyHelpField( {Lang("<Enter>") : Lang("Log out") })
        else:
            inPane.AddTitleField(Lang("Log In"))
            inPane.AddWrappedTextField(Lang("Press <Enter> to log in."))
            inPane.AddKeyHelpField( { Lang("<Enter>") : Lang("Log in") })

    @classmethod
    def ActivateHandler(cls):
        if Auth.Inst().IsAuthenticated():
            name = Auth.Inst().LoggedInUsername()
            Auth.Inst().LogOut()
            Data.Inst().Update()
            Layout.Inst().PushDialogue(InfoDialogue( Lang("User '")+name+Lang("' logged out")))
        else:
            Layout.Inst().PushDialogue(LoginDialogue())

    def Register(self):
        Importer.RegisterNamedPlugIn(
            self,
            'LOGINOUT', # Key of this plugin for replacement, etc.
            {
                'menuname' : 'MENU_AUTH',
                'menupriority' : 100,
                'menutext' : Lang('Log In/Out'),
                'statusupdatehandler' : XSFeatureLogInOut.StatusUpdateHandler,
                'activatehandler' : XSFeatureLogInOut.ActivateHandler
            }
        )

# Register this plugin when module is imported
XSFeatureLogInOut().Register()
