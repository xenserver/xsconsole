# Copyright (c) Citrix Systems 2008. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

if __name__ == "__main__":
    raise Exception("This script is a plugin for xsconsole and cannot run independently")
    
from XSConsoleStandard import *

class XSFeatureVMInfo:
    @classmethod
    def StatusUpdateHandler(cls, inPane):
        inPane.AddTitleField(Lang("Virtual Machine Information"))
    
        inPane.AddWrappedTextField(Lang(
            "Press <Enter> to display detailed information about each virtual machine on this host."))
        inPane.NewLine()
        inPane.AddWrappedTextField(Lang(
            "(Currently disabled)"))
    
    @classmethod
    def ActivateHandler(cls):
        Layout.Inst().TopDialogue().ChangeMenu('MENU_VMINFO')
    
    @classmethod
    def MenuRegenerator(cls, inName, inMenu):
        retVal = Menu(None, None, Lang("Customize System"), [
            ChoiceDef(Lang("Enter current filename"), None)
            ])
        return retVal
    
    def Register(self):
        Importer.RegisterMenuEntry(
            self,
            'MENU_VM', # Name of the menu this item is part of
            {
                'menuname' : 'MENU_VMINFO', # Name of the menu this item leads to when selected
                'menutext' : Lang('Virtual Machine Information'),
                'menupriority' : 100,
                'menuregenerator' : XSFeatureVMInfo.MenuRegenerator,
                #'activatehandler' : XSFeatureVMInfo.ActivateHandler,
                'statusupdatehandler' : XSFeatureVMInfo.StatusUpdateHandler
            }
        )

# Register this plugin when module is imported
XSFeatureVMInfo().Register()
