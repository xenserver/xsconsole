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

class VMUtils:
    operationNames = {
        # Only allow start on this host
        # 'start' : Struct(name = Lang("Start"), priority = 10),
        'start_on' : Struct(name = Lang("Start On This Host"), priority = 20),
        'suspend' : Struct(name = Lang("Suspend"), priority = 30),
        'resume' : Struct(name = Lang("Resume"), priority = 40),
        'clean_reboot' : Struct(name = Lang("Reboot"), priority = 50),
        'clean_shutdown' : Struct(name = Lang("Shut Down"), priority = 60),
        'pool_migrate' : Struct(name = Lang("Migrate"), priority = 70),
        'hard_reboot' : Struct(name = Lang("Force Reboot"), priority = 80),
        'hard_shutdown' : Struct(name = Lang("Force Shutdown"), priority = 90),
        'none' : Struct(name = Lang("No Operation"), priority = 100)
    }
    @classmethod
    def AllowedOperations(cls):
        return cls.operationNames.keys()
        
    @classmethod
    def AsyncOperation(cls, inOperation, inVMHandle, inParam0 = None):
        if inOperation == 'hard_reboot':
            task = Task.New(lambda x: x.xenapi.Async.VM.hard_reboot(inVMHandle.OpaqueRef()))
        elif inOperation == 'hard_shutdown':
            task = Task.New(lambda x: x.xenapi.Async.VM.hard_shutdown(inVMHandle.OpaqueRef()))
        elif inOperation == 'none':
            task = None # No operation
        elif inOperation == 'clean_reboot':
            task = Task.New(lambda x: x.xenapi.Async.VM.clean_reboot(inVMHandle.OpaqueRef()))
        elif inOperation == 'resume':
            task = Task.New(lambda x: x.xenapi.Async.VM.resume(inVMHandle.OpaqueRef(), False, True))
        elif inOperation == 'resume_on':
            task = Task.New(lambda x: x.xenapi.Async.VM.resume_on(inVMHandle.OpaqueRef(), inParam0.OpaqueRef(), False, True))
        elif inOperation == 'clean_shutdown':
            task = Task.New(lambda x: x.xenapi.Async.VM.clean_shutdown(inVMHandle.OpaqueRef()))
        elif inOperation == 'pool_migrate':
            if not isinstance(inParam0, HotOpaqueRef):
                raise Exception("Operation pool_migrate require a host HotOpaqueRef parameter")
            task = Task.New(lambda x: x.xenapi.Async.VM.pool_migrate(inVMHandle.OpaqueRef(), inParam0.OpaqueRef(), {}))
        elif inOperation == 'start':
            task = Task.New(lambda x: x.xenapi.Async.VM.start(inVMHandle.OpaqueRef(), False, True))
        elif inOperation == 'start_on':
            hostRef = HotAccessor().local_host_ref()
            task = Task.New(lambda x: x.xenapi.Async.VM.start_on(inVMHandle.OpaqueRef(), hostRef.OpaqueRef(), False, True))
        elif inOperation == 'suspend':
            task = Task.New(lambda x: x.xenapi.Async.VM.suspend(inVMHandle.OpaqueRef()))
        else:
            raise Exception("Unknown VM operation "+str(inOperation))
        
        return task
        
    @classmethod
    def DoOperation(cls, inOperation, inVMHandle, inParam0 = None):
        task = cls.AsyncOperation(inOperation, inVMHandle, inParam0)
        
        if task is not None:
            while task.IsPending():
                time.sleep(0.1)
            task.RaiseIfFailed()

    @classmethod
    def GetPossibleHostRefs(cls, inVMHandle):
        hostList = Task.Sync(lambda x: x.xenapi.VM.get_possible_hosts(inVMHandle.OpaqueRef()))
        hostList = [ HotOpaqueRef(host, 'host') for host in hostList ] # Convert OpaqueRefs to HotOpaqueRefs
        return hostList

    @classmethod
    def GetPossibleHostAccessors(cls, inVMHandle):
        # Convert host HotOpaqueRefs (from GetPossibleHostRefs) to HotAccessors for the hosts
        return [ HotAccessor().host[hostRef] for hostRef in cls.GetPossibleHostRefs(inVMHandle) ]

    @classmethod
    def OperationStruct(cls, inOperation):
        retVal = cls.operationNames.get(inOperation, None)
        if retVal is None:
            raise Exception("Unknown VM operation "+str(inOperation))
        return retVal

    @classmethod
    def OperationName(cls, inOperation):
        return cls.OperationStruct(inOperation).name

    @classmethod
    def OperationPriority(cls, inOperation):
        return cls.OperationStruct(inOperation).priority

    @classmethod
    def ReinstateVMs(cls, inHostRef, inVMRefList):
        for vmRef in inVMRefList:
            vm = HotAccessor().vm[vmRef]
            powerState = vm.power_state('').lower()
            if powerState.startswith('halted'):
                cls.DoOperation('start_on', vmRef, inHostRef)
            elif powerState.startswith('running'):
                cls.DoOperation('pool_migrate', vmRef, inHostRef)
            elif powerState.startswith('suspended'):
                cls.DoOperation('resume_on', vmRef, inHostRef)

class VMControlDialogue(Dialogue):
    def __init__(self, inVMHandle):
        self.vmHandle = inVMHandle
        Dialogue.__init__(self)
        self.operation = 'none'
        self.extraInfo = []
        self.opParams = []
        vm = HotAccessor().vm[self.vmHandle]
        allowedOps = vm.allowed_operations()

        choiceList = [ name for name in allowedOps if name in VMUtils.AllowedOperations() ]
        
        choiceList.sort(lambda x, y: cmp(VMUtils.OperationPriority(x), VMUtils.OperationPriority(y)))
        
        self.controlMenu = Menu()
        for choice in choiceList:
            self.controlMenu.AddChoice(name = VMUtils.OperationName(choice),
                onAction = self.HandleControlChoice,
                handle = choice)
        if self.controlMenu.NumChoices() == 0:
            self.controlMenu.AddChoice(name = Lang('<No Operations Available>'))
            
        self.ChangeState('INITIAL')
        
    def BuildPane(self):
        pane = self.NewPane(DialoguePane(self.parent))
        pane.TitleSet(Lang("Virtual Machine Control"))
        pane.AddBox()
        
        if self.state == 'MIGRATE':
            hosts = VMUtils.GetPossibleHostAccessors(self.vmHandle)
            hosts.sort(lambda x, y: cmp(x.name_label(), y.name_label()))
            self.hostMenu = Menu()
            residentHost = HotAccessor().vm[self.vmHandle].resident_on()
            for host in hosts:
                if host.HotOpaqueRef() != residentHost:
                    self.hostMenu.AddChoice(name = host.name_label(),
                        onAction = self.HandleHostChoice,
                        handle = host.HotOpaqueRef())
            if self.hostMenu.NumChoices() == 0:
                self.hostMenu.AddChoice(Lang('<No hosts available>'))

    def UpdateFieldsINITIAL(self):
        pane = self.Pane()
        pane.ResetFields()

        vm = HotAccessor().guest_vm[self.vmHandle]
        vmName = vm.name_label(None).encode('utf-8')
        if vmName is None:
            pane.AddTitleField(Lang("The Virtual Machine is no longer present"))
        else:
            pane.AddTitleField(vmName+Lang(" is ")+Lang(vm.power_state('<Unknown Power State>'))+'.')
        pane.AddMenuField(self.controlMenu)
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
    
    def UpdateFieldsMIGRATE(self):
        pane = self.Pane()
        pane.ResetFields()

        pane.AddTitleField(Lang('Please choose a new host for this Virtual Machine'))
        pane.AddMenuField(self.hostMenu)
        pane.AddKeyHelpField( { Lang("<Up/Down>") : Lang("Select"), Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
    
    def UpdateFieldsCONFIRM(self):
        pane = self.Pane()
        pane.ResetFields()

        vm = HotAccessor().vm[self.vmHandle]
        vmName = vm.name_label(None).encode('utf-8')
        if vmName is None:
            pane.AddTitleField(Lang("The Virtual Machine is no longer present"))
        else:
            pane.AddTitleField(Lang('Press <F8> to confirm this operation'))
            pane.AddStatusField(Lang("Operation", 20), VMUtils.OperationName(self.operation))
            pane.AddStatusField(Lang("Virtual Machine", 20), vmName)
            for values in self.extraInfo:
                pane.AddStatusField(values[0], values[1])
                
        pane.AddKeyHelpField( { Lang("<F8>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
    
    def UpdateFields(self):
        self.Pane().ResetPosition()
        getattr(self, 'UpdateFields'+self.state)() # Despatch method named 'UpdateFields'+self.state

    def ChangeState(self, inState):
        self.state = inState
        self.BuildPane()
        self.UpdateFields()
    
    def HandleKeyINITIAL(self, inKey):
        return self.controlMenu.HandleKey(inKey)

    def HandleKeyMIGRATE(self, inKey):
        return self.hostMenu.HandleKey(inKey)

    def HandleKeyCONFIRM(self, inKey):
        handled = False
        if inKey == 'KEY_F(8)':
            self.Commit()
            handled = True
        return handled

    def HandleKey(self,  inKey):
        handled = False
        if hasattr(self, 'HandleKey'+self.state):
            handled = getattr(self, 'HandleKey'+self.state)(inKey)
        
        if not handled and inKey == 'KEY_ESCAPE':
            Layout.Inst().PopDialogue()
            handled = True

        return handled
    
    def HandleControlChoice(self, inChoice):
        self.operation = inChoice
        if inChoice == 'pool_migrate':
            self.ChangeState('MIGRATE')
        else:
            self.ChangeState('CONFIRM')
        
    def HandleHostChoice(self, inChoice):
        self.opParams.append(inChoice)
        hostName = HotAccessor().vm[inChoice].name_label(Lang('<Unknown>'))
        self.extraInfo.append( (Lang('New Host', 20), hostName) ) # Append a tuple (so double brackets)
        self.ChangeState('CONFIRM')
        
    def Commit(self):
        Layout.Inst().PopDialogue()

        operationName = VMUtils.OperationName(self.operation)
        vmName = HotAccessor().guest_vm[self.vmHandle].name_label(Lang('<Unknown>')).encode('utf-8')
        messagePrefix = operationName + Lang(' operation on ') + vmName + ' '
        try:
            task = VMUtils.AsyncOperation(self.operation, self.vmHandle, *self.opParams)
            Layout.Inst().PushDialogue(ProgressDialogue(task, messagePrefix))
            
        except Exception, e:
            self.ChangeState('INITIAL')
            Layout.Inst().PushDialogue(InfoDialogue(messagePrefix + Lang("Failed"), Lang(e)))

class XSFeatureVMCommon:
    def Register(self):
        Importer.RegisterResource(
            self,
            'VM_COMMON', # Name of this item for replacement, etc.
            {
                'VMControlDialogue' : VMControlDialogue,
                'VMUtils' : VMUtils
            }
        )

# Register this plugin when module is imported
XSFeatureVMCommon().Register()
