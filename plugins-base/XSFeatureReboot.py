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

class XSFeatureReboot:
    @classmethod
    def StatusUpdateHandler(cls, inPane):
        inPane.AddTitleField(Lang("Reboot Server"))
    
        inPane.AddWrappedTextField(Lang(
            "Press <Enter> to reboot this server."))
    
        inPane.AddKeyHelpField( {
            Lang("<Enter>") : Lang("Reboot Server")
        } )

    @classmethod
    def RebootReplyHandler(cls,  inYesNo):
        if inYesNo == 'y':
            try:
                try:
                    Data.Inst().LocalHostDisable()
                except XenAPI.Failure:
                    raise
                except Exception, e:
                    # Ignore non-xapi failure - we want HA to veto the reboot but not other problems
                    XSLogFailure('Host disable before reboot failed', e)
                Layout.Inst().ExitBannerSet(Lang("Rebooting..."))
                Layout.Inst().ExitCommandSet('/sbin/shutdown -r now')
                XSLog('Initiating reboot')
            except Exception, e:
                Layout.Inst().PushDialogue(InfoDialogue(Lang("Reboot Failed"), Lang(e)))

    @classmethod
    def ActivateHandler(cls, inMessage = None):
        message = FirstValue(inMessage, Lang("Do you want to reboot this server?"))
        DialogueUtils.AuthenticatedOrPasswordUnsetOnly(lambda: Layout.Inst().PushDialogue(QuestionDialogue(
                message, lambda x: cls.RebootReplyHandler(x))))

    @classmethod
    def ReadyHandler(cls, inMessage = None):
        if State.Inst().RebootMessage() is not None and not (
               State.Inst().PasswordChangeRequired() or not Auth.Inst().IsPasswordSet()):
            cls.ActivateHandler(inMessage)
        
    def Register(self):
        Importer.RegisterNamedPlugIn(
            self,
            'REBOOT', # Key of this plugin for replacement, etc.
            {
                'menuname' : 'MENU_REBOOTSHUTDOWN',
                'menupriority' : 200,
                'menutext' : Lang('Reboot Server'),
                'statusupdatehandler' : XSFeatureReboot.StatusUpdateHandler,
                'activatehandler' : XSFeatureReboot.ActivateHandler,
                'readyhandler' : XSFeatureReboot.ReadyHandler,
                'readyhandlerpriority' : 1100,
            }
        )

# Register this plugin when module is imported
XSFeatureReboot().Register()
