# Copyright (c) Citrix Systems 2007. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

import re

from XSConsoleAuth import *
from XSConsoleBases import *
from XSConsoleConfig import *
from XSConsoleCurses import *
from XSConsoleData import *
from XSConsoleDialoguePane import *
from XSConsoleDialogueBases import *
from XSConsoleFields import *
from XSConsoleImporter import *
from XSConsoleLang import *
from XSConsoleMenus import *

class RootDialogue(Dialogue):
    
    def __init__(self, inLayout, inParent):
        Dialogue.__init__(self, inLayout, inParent)
        menuPane = self.NewPane(DialoguePane(self.parent, PaneSizerFixed(1, 2, 39, 21)), 'menu')
        menuPane.ColoursSet('MENU_BASE', 'MENU_BRIGHT', 'MENU_HIGHLIGHT', 'MENU_SELECTED')
        statusPane = self.NewPane(DialoguePane(self.parent, PaneSizerFixed(40, 2, 39, 21)), 'status')
        statusPane.ColoursSet('HELP_BASE', 'HELP_BRIGHT')
        self.menu = Importer.BuildRootMenu(self)
        self.UpdateFields()

    def UpdateFields(self):
        currentMenu = self.menu.CurrentMenu()
        currentChoiceDef = currentMenu.CurrentChoiceDef()

        menuPane = self.Pane('menu')
        menuPane.ResetFields()
        menuPane.ResetPosition()
        menuPane.AddTitleField(currentMenu.Title())
        # Scrolling doesn't work well for this menu because it's field is recreated on update.
        # Preserving the scroll position would improve it if there are more than 15 entries
        menuPane.AddMenuField(currentMenu, 15) # Allow extra height for this menu
        
        statusPane = self.Pane('status')

        try:
            statusPane.ResetFields()
            statusPane.ResetPosition()
            
            statusUpdateHandler = currentChoiceDef.StatusUpdateHandler()
            if statusUpdateHandler is not None:
                if currentChoiceDef.handle is not None:
                    statusUpdateHandler(statusPane, currentChoiceDef.handle)
                else:
                    statusUpdateHandler(statusPane)
                    
            else:
                raise Exception(Lang("Missing status handler"))

        except Exception, e:
            statusPane.ResetFields()
            statusPane.ResetPosition()
            statusPane.AddTitleField(Lang("Information not available"))
            statusPane.AddWrappedTextField(Lang(e))
        
        keyHash = { Lang("<Up/Down>") : Lang("Select") }
        if self.menu.CurrentMenu().Parent() != None:
            keyHash[ Lang("<Esc/Left>") ] = Lang("Back")
        else:
            if currentChoiceDef.OnAction() is not None:
                keyHash[ Lang("<Enter>") ] = Lang("OK")

        menuPane.AddKeyHelpField( keyHash )
        
        if statusPane.NumStaticFields() == 0: # No key help yet
            if statusPane.NeedsScroll():
                statusPane.AddKeyHelpField( {
                    Lang("<Page Up/Page Down>") : Lang("Scroll")
                })
    
    def HandleKey(self, inKey):
        currentMenu = self.menu.CurrentMenu()

        handled = currentMenu.HandleKey(inKey)

        if not handled and inKey == 'KEY_PPAGE':
            self.Pane('status').ScrollPageUp()
            handled = True
            
        if not handled and inKey == 'KEY_NPAGE':
            self.Pane('status').ScrollPageDown()
            handled = True
            
        if handled:
            self.UpdateFields()
            self.Pane('menu').Refresh()
            self.Pane('status').Refresh()
            
        return handled

    def ChangeMenu(self, inName):
        self.menu.SetMenu(inName, Importer.RegenerateMenu(inName, self.menu.GetMenu(inName)))
        self.menu.ChangeMenu(inName)
        self.menu.CurrentMenu().HandleEnter()
    
    def Reset(self):
        self.menu.Reset()
        self.UpdateFields()
        self.Pane('menu').Refresh()
        self.Pane('status').Refresh()
