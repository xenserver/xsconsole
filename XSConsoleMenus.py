
from XSConsoleBases import *

class ChoiceDef:
    def __init__(self, name, help, onAction = None, onEnter = None):
        ParamsToAttr()

class Menu:
    def __init__(self, inOwner, inParent, inTitle, inChoiceDefs):
        self.owner = inOwner
        self.parent = inParent
        self.title = inTitle
        self.choiceDefs = inChoiceDefs
        self.choiceIndex = 0

    def Parent(self): return self.parent
    def Title(self): return self.title
    def ChoiceDefs(self): return self.choiceDefs
    def ChoiceIndex(self): return self.choiceIndex

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
        if callable(self.CurrentChoiceDef().onEnter):
            self.CurrentChoiceDef().onEnter()
        return True

    def HandleSelect(self):
        if callable(self.CurrentChoiceDef().onAction):
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
        self.menus = {
            'MENU_ROOT' : Menu(self, None, "Customize System", [
                ChoiceDef("Status Display", "View the Status of this Machine",
                    None,  lambda : inDialogue.ChangeStatus('STATUS')),
                ChoiceDef("Authentication", "Set the root password to protect this machine",
                    lambda: inDialogue.ActivateDialogue('DIALOGUE_AUTH'), lambda : inDialogue.ChangeStatus('AUTH')),
                ChoiceDef("System Properties", "Configure the properties of this system",
                    lambda : inDialogue.ChangeMenu('MENU_PROPERTIES'), lambda : inDialogue.ChangeStatus('PROPERTIES')),
                ChoiceDef("Management Interface", "Configure the management interface for this system",
                    lambda : inDialogue.ChangeMenu('MENU_INTERFACE'), lambda : inDialogue.ChangeStatus('INTERFACE')),
                ChoiceDef("Server Reboot", "Reboot this server", "ServerReboot")
            ]),
            
            'MENU_PROPERTIES' : Menu(self, 'MENU_ROOT', "System Properties", [
                ChoiceDef("XenSource Product Information", "", None, lambda : inDialogue.ChangeStatus('XENSOURCE')),
                ChoiceDef("License Details", "", None, lambda : inDialogue.ChangeStatus('LICENCE')),
                ChoiceDef("Hostname", "", None, lambda : inDialogue.ChangeStatus('HOST')),
                ChoiceDef("System Details", "", None, lambda : inDialogue.ChangeStatus('SYSTEM')),
                ChoiceDef("Processor", "", None, lambda : inDialogue.ChangeStatus('PROCESSOR')),
                ChoiceDef("System Memory", "", None, lambda : inDialogue.ChangeStatus('MEMORY')),
                ChoiceDef("Local Storage Controller", ""),
                ChoiceDef("System Physical NICs", "", None, lambda : inDialogue.ChangeStatus('PIF')),
                ChoiceDef("BIOS Information", "", None, lambda : inDialogue.ChangeStatus('BIOS')),
                ChoiceDef("BMC Version", ""),
                ChoiceDef("CPLD Version", "")
            ]),

            'MENU_INTERFACE' : Menu(self, 'MENU_ROOT', "Management Interface", [
                ChoiceDef("Display NICs", "", None, lambda : inDialogue.ChangeStatus('PIF')),
                ChoiceDef("Select Management NIC", "",
                    lambda: inDialogue.ActivateDialogue('DIALOGUE_INTERFACE'), lambda : inDialogue.ChangeStatus('SELECTNIC')),
                ChoiceDef("Test Network", "", None, lambda : inDialogue.ChangeStatus('TESTNETWORK')),
            ])
        }

        self.currentKey = 'MENU_ROOT'
    
    def CurrentMenu(self):
        return self.menus[self.currentKey]

    def ChangeMenu(self, inKey):
        self.currentKey = inKey
        self.CurrentMenu().HandleEnter()
