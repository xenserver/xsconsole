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

class VerboseBootDialogue(Dialogue):
    def __init__(self):
        Dialogue.__init__(self)
        pane = self.NewPane(DialoguePane(self.parent))
        pane.TitleSet(Lang("Configure Verbose Boot Mode"))
        pane.AddBox()

        self.remoteShellMenu = Menu(self, None, Lang("Configure Verbose Boot Mode"), [
            ChoiceDef(Lang("Enable"), lambda: self.HandleChoice(True) ), 
            ChoiceDef(Lang("Disable"), lambda: self.HandleChoice(False) )
            ])
    
        self.UpdateFields()
        
    def UpdateFields(self):
        pane = self.Pane()
        pane.ResetFields()
        
        pane.AddTitleField(Lang("Please select an option"))
        pane.AddMenuField(self.remoteShellMenu)
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )

    def HandleKey(self, inKey):
        handled = self.remoteShellMenu.HandleKey(inKey)
        
        if not handled and inKey == 'KEY_ESCAPE':
            Layout.Inst().PopDialogue()
            handled = True

        return handled
                
    def HandleChoice(self, inChoice):
        data = Data.Inst()
        Layout.Inst().PopDialogue()
        Layout.Inst().TransientBanner(Lang("Updating..."))
        
        try:
            data.SetVerboseBoot(inChoice)
        except Exception, e:
            Layout.Inst().PushDialogue(InfoDialogue( Lang("Failed: ")+Lang(e)))
        else:
            Layout.Inst().PushDialogue(InfoDialogue( Lang("Configuration Updated")))


class XSFeatureVerboseBoot:
    @classmethod
    def StatusUpdateHandler(cls, inPane):
        data = Data.Inst()
        inPane.AddTitleField(Lang("Enable/Disable Verbose Boot Mode"))

        if State.Inst().VerboseBoot() is None:
            message = Lang('unknown.  To enable or disable')
        elif State.Inst().VerboseBoot():
            message = Lang('enabled.  To disable')
        else:
            message = Lang('disabled.  To enable')

        inPane.AddWrappedTextField(Lang(
            "This option will control the level of information displayed as this server boots.  "
            "The current state of verbose boot mode is ")+message+Lang(" press <Enter>."))
            
        inPane.AddKeyHelpField( { Lang("<Enter>") : Lang("Configure") } )  
        
    @classmethod
    def ActivateHandler(cls):
        DialogueUtils.AuthenticatedOnly(lambda: Layout.Inst().PushDialogue(VerboseBootDialogue()))
        
    def Register(self):
        data = Data.Inst()
        Importer.RegisterNamedPlugIn(
            self,
            'VERBOSE_BOOT', # Key of this plugin for replacement, etc.
            {
                'menuname' : 'MENU_TECHNICAL',
                'menupriority' : 400,
                'menutext' : Lang('Enable/Disable Verbose Boot Mode') ,
                'statusupdatehandler' : self.StatusUpdateHandler,
                'activatehandler' : self.ActivateHandler
            }
        )

# Register this plugin when module is imported
XSFeatureVerboseBoot().Register()
