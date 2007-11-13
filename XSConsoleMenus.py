
from XSConsoleBases import *
from XSConsoleLang import *

class ChoiceDef:
    def __init__(self, name, onAction = None, onEnter = None):
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

    def CurrentChoiceSet(self,  inChoice):
        self.choiceIndex = inChoice
        
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
            'MENU_ROOT' : Menu(self, None, Lang("Customize System"), [
                ChoiceDef(Lang("Status Display"), 
                    None,  lambda : inDialogue.ChangeStatus('STATUS')),
                ChoiceDef(Lang("Authentication"), 
                    lambda: inDialogue.ActivateDialogue('DIALOGUE_AUTH'), lambda : inDialogue.ChangeStatus('AUTH')),
                ChoiceDef(Lang("System Properties"), 
                    lambda : inDialogue.ChangeMenu('MENU_PROPERTIES'), lambda : inDialogue.ChangeStatus('PROPERTIES')),
                ChoiceDef(Lang("Management Interface"), 
                    lambda : inDialogue.ChangeMenu('MENU_INTERFACE'), lambda : inDialogue.ChangeStatus('INTERFACE')),
                ChoiceDef(Lang("Server Reboot"), 
                    lambda : inDialogue.ActivateDialogue('DIALOGUE_REBOOT'), lambda : inDialogue.ChangeStatus('REBOOT')), 
                ChoiceDef(Lang("Server Shutdown"), 
                    lambda : inDialogue.ActivateDialogue('DIALOGUE_SHUTDOWN'), lambda : inDialogue.ChangeStatus('SHUTDOWN')), 
                ChoiceDef(Lang("Local Command Shell"), 
                    lambda : inDialogue.ActivateDialogue('DIALOGUE_LOCALSHELL'), lambda : inDialogue.ChangeStatus('LOCALSHELL'))
            ]),
            
            'MENU_PROPERTIES' : Menu(self, 'MENU_ROOT', Lang("System Properties"), [
                ChoiceDef(Lang("XenServer Product Information"), None, lambda : inDialogue.ChangeStatus('XENSOURCE')),
                ChoiceDef(Lang("License Details"), None, lambda : inDialogue.ChangeStatus('LICENCE')),
                ChoiceDef(Lang("Hostname"), None, lambda : inDialogue.ChangeStatus('HOST')),
                ChoiceDef(Lang("System Details"), None, lambda : inDialogue.ChangeStatus('SYSTEM')),
                ChoiceDef(Lang("Processor"), None, lambda : inDialogue.ChangeStatus('PROCESSOR')),
                ChoiceDef(Lang("System Memory"), None, lambda : inDialogue.ChangeStatus('MEMORY')),
                ChoiceDef(Lang("Local Storage Controllers"), None, lambda : inDialogue.ChangeStatus('STORAGE')),
                ChoiceDef(Lang("System Physical NICs"),  None, lambda : inDialogue.ChangeStatus('PIF')),
                ChoiceDef(Lang("BIOS Information"), None, lambda : inDialogue.ChangeStatus('BIOS')),
                ChoiceDef(Lang("BMC Version"), None, lambda : inDialogue.ChangeStatus('BMC')),
                ChoiceDef(Lang("CPLD Version"), None, lambda : inDialogue.ChangeStatus('CPLD'))
            ]),

            'MENU_INTERFACE' : Menu(self, 'MENU_ROOT', Lang("Management Interface"), [
                ChoiceDef(Lang("Display NICs"), None, lambda : inDialogue.ChangeStatus('PIF')),
                ChoiceDef(Lang("Select Management NIC"),
                    lambda: inDialogue.ActivateDialogue('DIALOGUE_INTERFACE'), lambda : inDialogue.ChangeStatus('SELECTNIC')),
                ChoiceDef(Lang("Add/Remove DNS Servers"),
                    lambda: inDialogue.ActivateDialogue('DIALOGUE_DNS'), lambda : inDialogue.ChangeStatus('DNS')),
                ChoiceDef(Lang("Set Hostname"),
                    lambda: inDialogue.ActivateDialogue('DIALOGUE_HOSTNAME'), lambda : inDialogue.ChangeStatus('HOSTNAME')),
                ChoiceDef(Lang("Test Network"),
                    lambda: inDialogue.ActivateDialogue('DIALOGUE_TESTNETWORK'), lambda : inDialogue.ChangeStatus('TESTNETWORK'))
            ]),

            'MENU_AUTH' : Menu(self, 'MENU_ROOT', Lang("Authentication"), [
                ChoiceDef(Lang("Log Off"), lambda : inDialogue.HandleLogOff(), lambda : inDialogue.ChangeStatus('LOGOFF')),
                ChoiceDef(Lang("Change Password"),
                    lambda: inDialogue.ActivateDialogue('DIALOGUE_CHANGEPASSWORD'),
                    lambda : inDialogue.ChangeStatus('CHANGEPASSWORD')),
            ])
        }

        self.currentKey = 'MENU_ROOT'
    
    def CurrentMenu(self):
        return self.menus[self.currentKey]

    def ChangeMenu(self, inKey):
        self.currentKey = inKey
        self.CurrentMenu().HandleEnter()
