# Copyright (c) Citrix Systems 2008. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

if __name__ == "__main__":
    raise Exception("This script is a plugin for xsconsole and cannot run independently")
    
from XSConsoleStandard import *

class XSMenuOEMLayout:
    def UpdateFieldsBUR(self, inPane):
        inPane.AddTitleField(Lang("Backup, Restore and Update"))
    
        inPane.AddWrappedTextField(Lang(
            "From this menu you can backup and restore the system database, and apply "
            "software updates to the system."))
            
    def ActivateHandler(self, inName):
        Layout.Inst().TopDialogue().ChangeMenu(inName)

    def Register(self):
        data = Data.Inst()
        
        rootMenuDefs = [
            [ 'MENU_BUR', Lang("Backup, Restore and Update"),
                lambda: self.ActivateHandler('MENU_BUR'), self.UpdateFieldsBUR ],
        ]
        
        priority = 850
        for menuDef in rootMenuDefs:

            Importer.RegisterMenuEntry(
                self,
                'MENU_ROOT', # Name of the menu this item is part of
                {
                    'menuname' : menuDef[0], # Name of the menu this item leads to when selected
                    'menutext' : menuDef[1],
                    'menupriority' : priority,
                    'activatehandler' : menuDef[2],
                    'statusupdatehandler' : menuDef[3]
                }
            )
            priority += 100

# Register this plugin when module is imported
XSMenuOEMLayout().Register()
