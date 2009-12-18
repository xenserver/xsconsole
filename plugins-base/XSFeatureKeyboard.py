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

class KeyboardDialogue(Dialogue):
    def __init__(self):
        Dialogue.__init__(self)

        data=Data.Inst()
            
        choiceDefs = []
        
        namesToMaps = data.keyboard.namestomaps({})
        names = sorted(namesToMaps.keys())
        for name in names:
            choiceDefs.append(ChoiceDef(name, lambda: self.HandleNameChoice(namesToMaps[names[self.layoutMenu.ChoiceIndex()]]) ))

        choiceDefs.append(ChoiceDef(Lang('Choose Keymap File Directly'), lambda: self.HandleNameChoice(None)))

        self.layoutMenu = Menu(self, None, Lang("Select Keyboard Layout"), choiceDefs)

        choiceDefs = []
        
        keymaps = data.keyboard.keymaps({})
        keys = sorted(keymaps.keys())
        
        for key in keys:
            choiceDefs.append(ChoiceDef(key, lambda: self.HandleKeymapChoice(keys[self.keymapMenu.ChoiceIndex()]) ))
        
        self.keymapMenu = Menu(self, None, Lang("Select Keymap File"), choiceDefs)
    
        self.ChangeState('INITIAL')
        
    def BuildPane(self):            
        pane = self.NewPane(DialoguePane(self.parent))
        pane.TitleSet(Lang("Keyboard Language and Layout"))
        pane.AddBox()
        self.UpdateFields()
        
    def UpdateFieldsINITIAL(self):
        pane = self.Pane()
        pane.ResetFields()
        
        pane.AddTitleField(Lang("Please Select Your Keyboard Layout"))
        pane.AddMenuField(self.layoutMenu, 12) # There are a lot of names so make this menu high
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
            
    def UpdateFieldsKEYMAP(self):
        pane = self.Pane()
        pane.ResetFields()
        
        pane.AddTitleField(Lang("Please Select Your Keymap Name"))
        pane.AddMenuField(self.keymapMenu, 12) # There are a lot of keymaps so make this menu high
        pane.NewLine()
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
            
    def UpdateFields(self):
        self.Pane().ResetPosition()
        getattr(self, 'UpdateFields'+self.state)() # Despatch method named 'UpdateFields'+self.state
    
    def ChangeState(self, inState):
        self.state = inState
        self.BuildPane()
    
    def HandleKeyINITIAL(self, inKey):
        return self.layoutMenu.HandleKey(inKey)
     
    def HandleKeyKEYMAP(self, inKey):
        return self.keymapMenu.HandleKey(inKey)
     
    def HandleKey(self, inKey):
        handled = False
        if hasattr(self, 'HandleKey'+self.state):
            handled = getattr(self, 'HandleKey'+self.state)(inKey)
        
        if not handled and inKey == 'KEY_ESCAPE':
            Layout.Inst().PopDialogue()
            handled = True

        return handled
    
    def HandleNameChoice(self, inChoice):
        if inChoice is None:
            self.ChangeState('KEYMAP')
        else:
            try:
                self.Commit(inChoice)
            except Exception, e:
                Layout.Inst().PushDialogue(InfoDialogue( Lang("Missing keymap: ")+Lang(e)))
            
    def HandleKeymapChoice(self, inChoice):
        self.Commit(inChoice)
    
    def Commit(self, inKeymap):
        data=Data.Inst()
        Layout.Inst().PopDialogue()

        try:
            data.KeymapSet(inKeymap)
            message = Lang('Keyboard type set to ')+data.KeymapToName(inKeymap)
            Layout.Inst().PushDialogue(InfoDialogue( message))
            XSLog(message)
        except Exception, e:
            Layout.Inst().PushDialogue(InfoDialogue( Lang("Configuration failed: ")+Lang(e)))

        data.Update()


class XSFeatureKeyboard: 
    @classmethod
    def StatusUpdateHandler(cls, inPane):        
        data = Data.Inst()
        inPane.AddTitleField(Lang("Keyboard Language and Layout"))
        
        inPane.AddWrappedTextField(Lang("Use this option to select the correct language and layout for your keyboard."))
        inPane.NewLine()
        if data.keyboard.currentname('') != '':
            inPane.AddWrappedTextField(Lang("The current keyboard type is"))
            inPane.NewLine()
            inPane.AddWrappedTextField(data.keyboard.currentname(Lang('<Default>')))
            inPane.NewLine()
        
        inPane.AddKeyHelpField( {
            Lang("<Enter>") : Lang("Change Keyboard Type")
        })
        
    @classmethod
    def ActivateHandler(cls):
        # Allow without authentication, in case current keymap cannot enter the password
        Layout.Inst().PushDialogue(KeyboardDialogue())
        
    def Register(self):
        Importer.RegisterNamedPlugIn(
            self,
            'KEYBOARD', # Key of this plugin for replacement, etc.
            {
                'menuname' : 'MENU_MANAGEMENT',
                'menupriority' : 100,
                'menutext' : Lang('Keyboard Language and Layout') ,
                'statusupdatehandler' : self.StatusUpdateHandler,
                'activatehandler' : self.ActivateHandler
            }
        )

# Register this plugin when module is imported
XSFeatureKeyboard().Register()
