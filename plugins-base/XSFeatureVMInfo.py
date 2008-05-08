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
    def ResidentStatusUpdateHandler(cls, inPane):
        inPane.AddTitleField(Lang("Virtual Machine Information"))
    
        inPane.AddWrappedTextField(Lang(
            "Press <Enter> to display detailed information about Virtual Machines running on this host."))

    @classmethod
    def AllStatusUpdateHandler(cls, inPane):
        inPane.AddTitleField(Lang("Virtual Machine Information"))
    
        inPane.AddWrappedTextField(Lang(
            "Press <Enter> to display detailed information about all Virtual Machines in the Pool."))

    @classmethod
    def NoVMStatusUpdateHandler(cls, inPane):
        inPane.AddTitleField(Lang("Virtual Machine Information"))

        inPane.AddWrappedTextField(Lang("There are no Virtual Machines on this host."))

    @classmethod
    def InfoStatusUpdateHandler(cls, inPane, inHandle):
        vm = HotAccessor().vm[inHandle]
        if vm is None:
            inPane.AddWrappedTextField(Lang("This Virtual Machine is no longer present"))
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
    
                try:
                    networks = vm.guest_metrics.networks({})
                    for key in sorted(networks.keys()):
                        inPane.AddStatusField((Lang('Network ')+key).ljust(16,  ' '), networks[key])
                except Exception, e:
                    inPane.AddStatusField(Lang('Network Info', 16), Lang('<Unavailable>'))
                    
        inPane.AddKeyHelpField( { Lang("<Enter>") : Lang("Control This Virtual Machine") } )
    
    @classmethod
    def ResidentActivateHandler(cls):
        Layout.Inst().TopDialogue().ChangeMenu('MENU_RESIDENTVM')
    
    @classmethod
    def AllActivateHandler(cls):
        Layout.Inst().TopDialogue().ChangeMenu('MENU_ALLVM')
    
    @classmethod
    def InfoActivateHandler(cls, inHandle):
        dialogue = Importer.GetResource('VMControlDialogue')
        DialogueUtils.AuthenticatedOnly(lambda: Layout.Inst().PushDialogue(dialogue(inHandle)))
    
    @classmethod
    def MenuRegenerator(cls, inList, inMenu):
        retVal = copy.copy(inMenu)
        retVal.RemoveChoices()
        # inList is a list of HotOpaqueRef objects
        vmList = [ HotAccessor().vm[x] for x in inList ]
        # Sort list by VM name
        vmList.sort(lambda x,y: cmp(x.name_label(''), y.name_label('')))
        
        for vm in vmList:
            nameLabel = vm.name_label(Lang('<Unknown>'))
            if not vm.is_control_domain(True) and not vm.is_a_template(True):
                retVal.AddChoice(name = nameLabel,
                                            onAction = cls.InfoActivateHandler,
                                            statusUpdateHandler = cls.InfoStatusUpdateHandler,
                                            handle = vm.HotOpaqueRef())
            
        if retVal.NumChoices() == 0:
            retVal.AddChoice(name = Lang('<No Virtual Machines Present>'),
                                        statusUpdateHandler = cls.NoVMStatusUpdateHandler)
            
        return retVal
    
    @classmethod
    def ResidentMenuRegenerator(cls, inName, inMenu):
        return cls.MenuRegenerator(HotAccessor().local_host.resident_VMs([]), inMenu)
    
    @classmethod
    def AllMenuRegenerator(cls, inName, inMenu):
        return cls.MenuRegenerator(HotAccessor().guest_vm({}).keys(), inMenu)
    
    def Register(self):
        Importer.RegisterMenuEntry(
            self,
            'MENU_VM', # Name of the menu this item is part of
            {
                'menuname' : 'MENU_RESIDENTVM', # Name of the menu this item leads to when selected
                'menutext' : Lang('VMs Running On This Host'),
                'menupriority' : 100,
                'menuregenerator' : XSFeatureVMInfo.ResidentMenuRegenerator,
                'activatehandler' : XSFeatureVMInfo.ResidentActivateHandler,
                'statusupdatehandler' : XSFeatureVMInfo.ResidentStatusUpdateHandler
            }
        )

        Importer.RegisterMenuEntry(
            self,
            'MENU_VM', # Name of the menu this item is part of
            {
                'menuname' : 'MENU_ALLVM', # Name of the menu this item leads to when selected
                'menutext' : Lang('All VMs'),
                'menupriority' : 300,
                'menuregenerator' : XSFeatureVMInfo.AllMenuRegenerator,
                'activatehandler' : XSFeatureVMInfo.AllActivateHandler,
                'statusupdatehandler' : XSFeatureVMInfo.AllStatusUpdateHandler
            }
        )

# Register this plugin when module is imported
XSFeatureVMInfo().Register()
