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
    
    @classmethod
    def NoVMStatusUpdateHandler(cls, inPane):
        inPane.AddTitleField(Lang("Virtual Machine Information"))

        inPane.AddWrappedTextField(Lang("There are no virtual machines on this host."))

    
    @classmethod
    def InfoStatusUpdateHandler(cls, inPane, inHandle):
        inPane.AddTitleField(Lang("Virtual Machine Information"))
    
        vm = HotAccessor().guest_vm(inHandle)
        if vm is None:
            inPane.AddWrappedTextField(Lang("This virtual machine is no longer present"))
        else:
            inPane.AddWrappedTextField(vm.Get('name_label'))
            inPane.NewLine()
            try:
                inPane.AddStatusField(Lang("Total Memory", 16), vm.Get('guest_metrics')['memory']['total']+' KB')
                inPane.AddStatusField(Lang("Free Memory", 16), vm.Get('guest_metrics')['memory']['free']+' KB')
            except Exception, e:
                pass
    
    @classmethod
    def ActivateHandler(cls):
        Layout.Inst().TopDialogue().ChangeMenu('MENU_VMINFO')
    
    @classmethod
    def MenuRegenerator(cls, inName, inMenu):
        retVal = copy.copy(inMenu)
        retVal.RemoveChoices()
        for key, vm in HotData.Inst().guest_vm({}).iteritems():
            nameLabel = vm.get('name_label', Lang('<Unknown>'))
            retVal.AddChoice(name = nameLabel,
                                        statusUpdateHandler = cls.InfoStatusUpdateHandler,
                                        handle = key)
            
        if retVal.NumChoices() == 0:
            retVal.AddChoice(name = Lang('<No Virtual Machines Present>'),
                                        statusUpdateHandler = cls.NoVMStatusUpdateHandler)
            
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
                'activatehandler' : XSFeatureVMInfo.ActivateHandler,
                'statusupdatehandler' : XSFeatureVMInfo.StatusUpdateHandler
            }
        )

# Register this plugin when module is imported
XSFeatureVMInfo().Register()
