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
        vm = HotAccessor().guest_vm(inHandle)
        if vm is None:
            inPane.AddWrappedTextField(Lang("This virtual machine is no longer present"))
        else:
            powerState = vm.power_state(Lang('<Unknown>'))
            isRunning = powerState.lower().startswith('running')
            inPane.AddWrappedTextField(vm.name_label())
            inPane.NewLine()
            inPane.AddStatusField(Lang("Power State", 16), powerState)
            inPane.AddStatusField(Lang("Memory", 16), SizeUtils.MemorySizeString(vm.memory_static_max(0)))
            try:
                if isRunning:
                    perCPUUsage = vm.metrics.VCPUs_utilisation({})

                    cpuUsage = sum(perCPUUsage.values()) / len(perCPUUsage) # Let divide by zero throw
                    cpuUsage = max(0, min(cpuUsage, 1))
                    cpuUsageStr = "%d%% of %d CPUs" % (int(cpuUsage * 100), len(perCPUUsage))
                else:
                    cpuUsageStr = '-' # Follow XenCenter convention

            except Exception, e:
                cpuUsageStr = Lang('<Unknown>')
            
            inPane.AddStatusField(Lang("CPU Usage", 16), cpuUsageStr)

            if isRunning:
                try:
                    freeMemoryKB = vm.guest_metrics.memory({})['free'] # returns a string or throws
                    freeMemory = int(freeMemoryKB) * 1024.0 # int converts from string here
                    usedMemory = int(vm.memory_static_max(0)) - freeMemory
                    memoryUsage = usedMemory / int(vm.memory_static_max(1))
                    memoryUsage = max(0, min(memoryUsage, 1))
                    memoryUsageStr = "%d%% (%s)" % (int(memoryUsage * 100), SizeUtils.MemorySizeString(usedMemory))
                except Exception, e:
                    memoryUsageStr = Lang('<Unavailable>')
                    
                inPane.AddStatusField(Lang("Memory Usage", 16), memoryUsageStr)
    
        inPane.AddKeyHelpField( { Lang("<Enter>") : Lang("Control This Virtual Machine") } )
    
    @classmethod
    def ActivateHandler(cls):
        Layout.Inst().TopDialogue().ChangeMenu('MENU_VMINFO')
    
    @classmethod
    def InfoActivateHandler(cls, inHandle):
        dialogue = Importer.GetResource('VMControlDialogue')
        DialogueUtils.AuthenticatedOnly(lambda: Layout.Inst().PushDialogue(dialogue(inHandle)))
    
    @classmethod
    def MenuRegenerator(cls, inName, inMenu):
        retVal = copy.copy(inMenu)
        retVal.RemoveChoices()
        for key, vm in HotData.Inst().guest_vm({}).iteritems():
            nameLabel = vm.get('name_label', Lang('<Unknown>'))
            retVal.AddChoice(name = nameLabel,
                                        onAction = cls.InfoActivateHandler,
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
