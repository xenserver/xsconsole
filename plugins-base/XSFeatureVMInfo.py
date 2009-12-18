# Copyright (c) 2008-2009 Citrix Systems Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 only.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

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
            try:
                vmMetrics = HotMetrics.Inst().VMMetrics(vm.uuid())
            except Exception, e:
                XSLogFailure('VMMetrics failed', e)
                vmMetrics = {}
            
            powerState = vm.power_state(Lang('<Unknown>'))
            isRunning = powerState.lower().startswith('running')
            inPane.AddWrappedTextField(vm.name_label())
            inPane.NewLine()
            inPane.AddStatusField(Lang("Power State", 16), powerState)
            inPane.AddStatusField(Lang("Memory", 16), SizeUtils.MemorySizeString(vm.memory_static_max(0)))
            try:
                cpuUsage = vmMetrics['cpuusage']
                numCPUs = vmMetrics['numcpus']
                if isRunning and cpuUsage is not None:
                    cpuUsage = max(0, min(cpuUsage, 1))
                    cpuUsageStr = "%d%% of %d CPUs" % (int(cpuUsage * 100), numCPUs)
                else:
                    cpuUsageStr = Lang('<Unavailable>')

            except Exception, e:
                cpuUsageStr = Lang('<Unknown>')
            
            inPane.AddStatusField(Lang("CPU Usage", 16), cpuUsageStr)

            if isRunning:
                try:
                    totalMemory = vmMetrics['memory_total']
                    freeMemory = vmMetrics['memory_free']

                    usedMemory = totalMemory - freeMemory
                    memoryUsage = usedMemory / totalMemory
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
        vmIDs = Task.Sync(lambda x: x.xenapi.VM.get_all())
        if len(vmIDs) > 100:
            Layout.Inst().PushDialogue(InfoDialogue(Lang('This feature is unavailable in Pools with more than 100 Virtual Machines')))
        else:
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
        # Fetching all guest_vm is an expensive operation (implies xenapi.vm.get_all_records)
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
