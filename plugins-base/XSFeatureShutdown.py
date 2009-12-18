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

class XSFeatureShutdown:
    @classmethod
    def StatusUpdateHandler(cls, inPane):
        inPane.AddTitleField(Lang("Shutdown Server"))
    
        inPane.AddWrappedTextField(Lang(
            "Press <Enter> to shutdown this server."))
    
        inPane.AddKeyHelpField( {
            Lang("<Enter>") : Lang("Shutdown Server")
        } )

    @classmethod
    def ShutdownReplyHandler(cls,  inYesNo):
        if inYesNo == 'y':
            try:
                try:
                    Data.Inst().LocalHostDisable()
                except XenAPI.Failure:
                    raise
                except Exception, e:
                    # Ignore non-xapi failure - we want HA to veto the shutdown but not other problems
                    XSLogFailure('Host disable before shutdown failed', e)
                Layout.Inst().ExitBannerSet(Lang("Shutting Down..."))
                Layout.Inst().ExitCommandSet('/sbin/shutdown -h now')
                XSLog('Initiated shutdown')
            except Exception, e:
                Layout.Inst().PushDialogue(InfoDialogue(Lang("Shutdown Failed"), Lang(e)))

    @classmethod
    def ActivateHandler(cls, *inParams):
        if len(inParams) > 0:
            banner = inParams[0]
        else:
            banner = Lang("Do you want to shutdown this server?")
        DialogueUtils.AuthenticatedOrPasswordUnsetOnly(lambda: Layout.Inst().PushDialogue(QuestionDialogue(banner, lambda x: cls.ShutdownReplyHandler(x))))
        
    def Register(self):
        Importer.RegisterNamedPlugIn(
            self,
            'SHUTDOWN', # Key of this plugin for replacement, etc.
            {
                'menuname' : 'MENU_REBOOTSHUTDOWN',
                'menupriority' : 300,
                'menutext' : Lang('Shutdown Server'),
                'statusupdatehandler' : XSFeatureShutdown.StatusUpdateHandler,
                'activatehandler' : XSFeatureShutdown.ActivateHandler
            }
        )

# Register this plugin when module is imported
XSFeatureShutdown().Register()
