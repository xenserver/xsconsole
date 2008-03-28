# Copyright (c) Citrix Systems 2007. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

import sys

from pprint import pprint

from XSConsoleBases import *
from XSConsoleConfig import *
from XSConsoleData import *
from XSConsoleImporter import *
from XSConsoleLang import *

class ChoiceDef:
    def __init__(self, name, onAction = None, onEnter = None, priority = None, statusUpdateHandler = None, handle = None):
        ParamsToAttr()
        
    def StatusUpdateHandler(self):
        return self.statusUpdateHandler
        
    def StatusUpdateHandlerSet(self, inHandler):
        self.statusUpdateHandler = inHandler
        
    def OnAction(self):
        return self.onAction

class Menu:
    def __init__(self, inOwner, inParent, inTitle, inChoiceDefs = None):
        self.owner = inOwner
        self.parent = inParent
        self.title = inTitle
        self.choiceDefs = FirstValue(inChoiceDefs, [])
        self.choiceIndex = 0
        self.defaultPriority=1000
        for choice in self.choiceDefs:
            if choice.priority is None:
                choice.priority = self.defaultPriority
                self.defaultPriority += 100

    def Parent(self): return self.parent
    def ParentSet(self, inParent): self.parent = inParent
    def Title(self): return self.title
    def TitleSet(self, inTitle): self.title = inTitle
    def ChoiceDefs(self): return self.choiceDefs
    def ChoiceIndex(self): return self.choiceIndex
    def NumChoices(self): return len(self.choiceDefs)

    def AddChoiceDef(self, inChoiceDef, inPriority = None):
        if inPriority is None:
            priority = self.defaultPriority
            self.defaultPriority += 100
        else:
            priority = inPriority
        
        inChoiceDef.priority = priority # FIXME (modifies input parameter)
        self.choiceDefs.append(inChoiceDef)
        
        self.choiceDefs.sort(lambda x, y : cmp(x.priority, y.priority))

    def AddChoice(self, name, onAction = None, onEnter = None, priority = None, statusUpdateHandler = None, handle = None):
        choiceDef = ChoiceDef(name, onAction, onEnter, priority, statusUpdateHandler, handle)
        self.AddChoiceDef(choiceDef)
        
    def RemoveChoices(self):
        self.choiceDefs = []
        self.choiceIndex = 0
        self.defaultPriority=1000
            
    def CurrentChoiceSet(self,  inChoice):
        self.choiceIndex = inChoice
        # Also need to call HandleEnter
        
    def CurrentChoiceDef(self):
        return self.choiceDefs[self.choiceIndex]

    def HandleArrowDown(self):
        self.choiceIndex += 1
        if self.choiceIndex >= len(self.choiceDefs):
            self.choiceIndex = 0
        self.HandleEnter()
        return True

    def HandleArrowUp(self):
        if self.choiceIndex == 0:
            self.choiceIndex = len(self.choiceDefs) - 1
        else:
            self.choiceIndex -= 1
        self.HandleEnter()
        return True

    def HandleArrowLeft(self):
        if self.parent:
            self.owner.ChangeMenu(self.parent)
            handled = True
        else:
            handled = False
        return handled

    def HandleEnter(self):
        choiceDef = self.CurrentChoiceDef()
        if callable(choiceDef.onEnter):
            if choiceDef.handle is not None:
                self.CurrentChoiceDef().onEnter(choiceDef.handle)
            else:
                self.CurrentChoiceDef().onEnter()
        return True

    def HandleSelect(self):
        choiceDef = self.CurrentChoiceDef()
        if callable(choiceDef.onAction):
            if choiceDef.handle is not None:
                self.CurrentChoiceDef().onAction(choiceDef.handle)
            else:
                self.CurrentChoiceDef().onAction()
        return True

    def HandleKey(self, inKey):
        if inKey == 'KEY_DOWN':
            handled = self.HandleArrowDown()
        elif inKey == 'KEY_UP':
            handled = self.HandleArrowUp()
        elif inKey == 'KEY_LEFT' or inKey == 'KEY_ESCAPE':
            handled = self.HandleArrowLeft()
        elif inKey == 'KEY_ENTER' or inKey == 'KEY_RIGHT':
            handled = self.HandleSelect()
        else:
            handled = False
        
        return handled
        
class RootMenu:
    def __init__(self, inDialogue):
        self.menus = {'MENU_ROOT' : Menu(self, None, Lang("Customize System"), [ ]) }
        self.currentKey = 'MENU_ROOT'
    
    def GetMenu(self, inMenuName):
        retVal = self.menus.get(inMenuName, None)
        if retVal is None:
            raise Exception(Lang("Unknown menu '")+inMenuName+"'")
        return retVal
        
    def SetMenu(self, inMenuName, inMenu):
        self.menus[inMenuName] = inMenu
        
    def CurrentMenu(self):
        return self.menus[self.currentKey]

    def CurrentMenuSet(self, inMenu):
        self.menus[self.currentKey] = inMenu

    def ChangeMenu(self, inKey):
        self.currentKey = inKey
        self.CurrentMenu().HandleEnter()

    def Reset(self):
        self.currentKey = 'MENU_ROOT'
        
        for menu in self.menus.values():
            menu.CurrentChoiceSet(0)
            
        self.CurrentMenu().HandleEnter()
        
    def AddChoice(self, inMenuName, inChoiceDef, inPriority = None):
        if not self.menus.has_key(inMenuName):
            raise Exception(Lang("Unknown menu '")+inMenuName+"'")
        
        self.menus[inMenuName].AddChoiceDef(inChoiceDef, inPriority)

    def CreateMenuIfNotPresent(self, inName, inTitle = None, inParent = None):
        if inName not in self.menus:
            self.menus[inName] = Menu(self, FirstValue(inParent, inName), FirstValue(inTitle, ''))
        else:
            # Menus can be created without parent and title, which are supplied
            # by a later call.  Handle this here.
            if inParent is not None:
                self.menus[inName].ParentSet(inParent)
            if inTitle is not None:
                self.menus[inName].TitleSet(inTitle)
