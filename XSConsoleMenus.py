# Copyright (c) Citrix Systems 2007. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

from pprint import pprint

from XSConsoleBases import *
from XSConsoleConfig import *
from XSConsoleData import *
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
        # Also need to can HandleEnter
        
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
        rootMenu = Menu(self, None, Lang("Customize System"), [
            ChoiceDef(Lang("Status Display"), 
                None,  lambda : inDialogue.ChangeStatus('STATUS')),
            ChoiceDef(Lang("Authentication"), 
                lambda: inDialogue.ChangeMenu('MENU_AUTH'), lambda : inDialogue.ChangeStatus('AUTH')),
            ChoiceDef(Lang("System Properties"), 
                lambda : inDialogue.ChangeMenu('MENU_PROPERTIES'), lambda : inDialogue.ChangeStatus('PROPERTIES')),
            ChoiceDef(Lang("Server Management"), 
                lambda : inDialogue.ChangeMenu('MENU_INTERFACE'), lambda : inDialogue.ChangeStatus('INTERFACE')),
            ChoiceDef(Lang("Backup, Restore and Update"), 
                lambda : inDialogue.ChangeMenu('MENU_BURP'), lambda : inDialogue.ChangeStatus('BURP')),
            ChoiceDef(Lang("Technical Support"), 
                lambda : inDialogue.ChangeMenu('MENU_TECHNICAL'), lambda : inDialogue.ChangeStatus('TECHNICAL')),
            ChoiceDef(Lang("Reboot or Shutdown"), 
                lambda : inDialogue.ChangeMenu('MENU_REBOOT'), lambda : inDialogue.ChangeStatus('REBOOTSHUTDOWN')),
            ChoiceDef(Lang("Local Command Shell"), 
                lambda : inDialogue.ActivateDialogue('DIALOGUE_LOCALSHELL'), lambda : inDialogue.ChangeStatus('LOCALSHELL'))
        ])
        rebootText = Lang("Reboot Server")
        
        propertiesChoices = [
                ChoiceDef(Lang("XenServer Product Information"), None, lambda : inDialogue.ChangeStatus('XENSERVER')),
                ChoiceDef(Lang("License Details"), None, lambda : inDialogue.ChangeStatus('LICENCE')),
                ChoiceDef(Lang("Hostname"), None, lambda : inDialogue.ChangeStatus('HOST')),
                ChoiceDef(Lang("System Details"), None, lambda : inDialogue.ChangeStatus('SYSTEM')),
                ChoiceDef(Lang("Processor"), None, lambda : inDialogue.ChangeStatus('PROCESSOR')),
                ChoiceDef(Lang("System Memory"), None, lambda : inDialogue.ChangeStatus('MEMORY')),
                ChoiceDef(Lang("Local Storage Controllers"), None, lambda : inDialogue.ChangeStatus('STORAGE')),
                ChoiceDef(Lang("System Physical NICs"),  None, lambda : inDialogue.ChangeStatus('PIF')),
                ChoiceDef(Lang("BIOS Information"), None, lambda : inDialogue.ChangeStatus('BIOS'))
            ]

        if Data.Inst().bmc.version('') != '':
           propertiesChoices.append(ChoiceDef(Lang("BMC Version"), None, lambda : inDialogue.ChangeStatus('BMC')))
           
        if Data.Inst().cpld.version('') != '':
            propertiesChoices.append(ChoiceDef(Lang("CPLD Version"), None, lambda : inDialogue.ChangeStatus('CPLD')))
        
        burpChoices = [
            ChoiceDef(Lang("Apply Patch or Update"), lambda: inDialogue.ActivateDialogue('DIALOGUE_PATCH'),
                lambda : inDialogue.ChangeStatus('PATCH')),
            ChoiceDef(Lang("Backup Server State"), lambda: inDialogue.ActivateDialogue('DIALOGUE_BACKUP'),
                lambda : inDialogue.ChangeStatus('BACKUP')),
            ChoiceDef(Lang("Restore Server State From Backup"), lambda: inDialogue.ActivateDialogue('DIALOGUE_RESTORE'),
                lambda : inDialogue.ChangeStatus('RESTORE'))
        ]
            
        if Data.Inst().backup.canrevert(False):
            burpChoices.append(ChoiceDef(Lang("Revert to Pre-Patch Version"), lambda: inDialogue.ActivateDialogue('DIALOGUE_REVERT'),
                lambda : inDialogue.ChangeStatus('REVERT')))
        
        self.menus = {
            'MENU_ROOT' : rootMenu,
            
            'MENU_PROPERTIES' : Menu(self, 'MENU_ROOT', Lang("System Properties"), propertiesChoices),

            'MENU_INTERFACE' : Menu(self, 'MENU_ROOT', Lang("Server Management"), [
                ChoiceDef(Lang("Display NICs"), None, lambda : inDialogue.ChangeStatus('PIF')),
                ChoiceDef(Lang("Select Management NIC"),
                    lambda: inDialogue.ActivateDialogue('DIALOGUE_INTERFACE'), lambda : inDialogue.ChangeStatus('SELECTNIC')),
                ChoiceDef(Lang("Add/Remove DNS Servers"),
                    lambda: inDialogue.ActivateDialogue('DIALOGUE_DNS'), lambda : inDialogue.ChangeStatus('DNS')),
                ChoiceDef(Lang("Set Hostname"),
                    lambda: inDialogue.ActivateDialogue('DIALOGUE_HOSTNAME'), lambda : inDialogue.ChangeStatus('HOSTNAME')),
                ChoiceDef(Lang("Remote Logging (syslog)"),
                    lambda: inDialogue.ActivateDialogue('DIALOGUE_SYSLOG'), lambda : inDialogue.ChangeStatus('SYSLOG')),
                ChoiceDef(Lang("Disks and Storage Repositories"),
                    lambda: inDialogue.ActivateDialogue('DIALOGUE_SR'), lambda : inDialogue.ChangeStatus('SR')),
                ChoiceDef(Lang("Setup Remote Database"),
                    lambda: inDialogue.ActivateDialogue('DIALOGUE_REMOTEDB'), lambda : inDialogue.ChangeStatus('REMOTEDB')),
                ChoiceDef(Lang("Install License File"), lambda: inDialogue.ActivateDialogue('DIALOGUE_INSTALLLICENCE'),
                    lambda : inDialogue.ChangeStatus('INSTALLLICENCE')),
                ChoiceDef(Lang("Test Network"),
                    lambda: inDialogue.ActivateDialogue('DIALOGUE_TESTNETWORK'), lambda : inDialogue.ChangeStatus('TESTNETWORK'))
            ]),

            'MENU_AUTH' : Menu(self, 'MENU_ROOT', Lang("Authentication"), [
                ChoiceDef(Lang("Log In/Out"), lambda : inDialogue.HandleLogInOut(), lambda : inDialogue.ChangeStatus('LOGINOUT')),
                ChoiceDef(Lang("Change Password"),
                    lambda: inDialogue.ActivateDialogue('DIALOGUE_CHANGEPASSWORD'),
                    lambda : inDialogue.ChangeStatus('CHANGEPASSWORD')),
                ChoiceDef(Lang("Change Auto-Logout Time"),
                    lambda: inDialogue.ActivateDialogue('DIALOGUE_CHANGETIMEOUT'),
                    lambda : inDialogue.ChangeStatus('CHANGETIMEOUT'))
            ]), 
 
         'MENU_BURP' : Menu(self, 'MENU_ROOT', Lang("Backup, Restore and Patch"), burpChoices),
            
        'MENU_TECHNICAL' : Menu(self, 'MENU_ROOT', Lang("Technical Support"), [
            ChoiceDef(Lang("Enable/Disable Remote Shell"), lambda: inDialogue.ActivateDialogue('DIALOGUE_REMOTESHELL'),
                lambda : inDialogue.ChangeStatus('REMOTESHELL')),
            ChoiceDef(Lang("Validate Server Configuration"), lambda: inDialogue.ActivateDialogue('DIALOGUE_VALIDATE'),
                lambda : inDialogue.ChangeStatus('VALIDATE')),
            ChoiceDef(Lang("Upload Bug Report"), lambda: inDialogue.ActivateDialogue('DIALOGUE_BUGREPORT'),
                lambda : inDialogue.ChangeStatus('BUGREPORT')) ,
            ChoiceDef(Lang("Save Bug Report"), lambda: inDialogue.ActivateDialogue('DIALOGUE_SAVEBUGREPORT'),
                lambda : inDialogue.ChangeStatus('SAVEBUGREPORT')),
            ChoiceDef(Lang("Enable/Disable Verbose Boot Mode"), lambda: inDialogue.ActivateDialogue('DIALOGUE_VERBOSEBOOT'),
                lambda : inDialogue.ChangeStatus('VERBOSEBOOT')),
            ChoiceDef(Lang("Reset to Factory Defaults"), lambda: inDialogue.ActivateDialogue('DIALOGUE_RESET'),
                lambda : inDialogue.ChangeStatus('RESET'))
        ]), 
 
        'MENU_REBOOT' : Menu(self, 'MENU_ROOT', Lang("Reboot"), [
                ChoiceDef(rebootText, 
                    lambda : inDialogue.ActivateDialogue('DIALOGUE_REBOOT'), lambda : inDialogue.ChangeStatus('REBOOT')), 
                ChoiceDef(Lang("Shutdown Server"), 
                    lambda : inDialogue.ActivateDialogue('DIALOGUE_SHUTDOWN'), lambda : inDialogue.ChangeStatus('SHUTDOWN')), 
            ])
        }
        
        self.currentKey = 'MENU_ROOT'
    
    def CurrentMenu(self):
        return self.menus[self.currentKey]

    def ChangeMenu(self, inKey):
        self.currentKey = inKey
        self.CurrentMenu().HandleEnter()
