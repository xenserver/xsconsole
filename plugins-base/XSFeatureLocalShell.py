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

class XSFeatureLocalShell:
    @classmethod
    def StatusUpdateHandler(cls, inPane):
        inPane.AddTitleField(Lang("Local Command Shell"))
    
        inPane.AddWrappedTextField(Lang(
            "Press <Enter> to start a local command shell on this server.  "
            "This shell will have root privileges."))
    
    @classmethod
    def StartLocalShell(self):
        user = os.environ.get('USER', 'root')
        Layout.Inst().ExitBannerSet(Lang("\rShell for local user '")+user+"'.\r\r"+
                Lang("Type 'exit' to return to the management console.\r"))
        Layout.Inst().SubshellCommandSet("( export HOME=/root; export TMOUT="+str(State.Inst().AuthTimeoutSeconds())+" && cat /etc/motd && /bin/bash --login )")
        XSLog('Local shell')
        
    @classmethod
    def ActivateHandler(cls):
        DialogueUtils.AuthenticatedOnly(lambda: cls.StartLocalShell())
        
    def Register(self):
        Importer.RegisterNamedPlugIn(
            self,
            'LOCAL_SHELL', # Key of this plugin for replacement, etc.
            {
                'menuname' : 'MENU_ROOT',
                'menupriority' : 1500,
                'menutext' : Lang('Local Command Shell'),
                'statusupdatehandler' : XSFeatureLocalShell.StatusUpdateHandler,
                'activatehandler' : XSFeatureLocalShell.ActivateHandler
            }
        )

# Register this plugin when module is imported
XSFeatureLocalShell().Register()
