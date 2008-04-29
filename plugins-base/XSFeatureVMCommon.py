# Copyright (c) Citrix Systems 2008. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

if __name__ == "__main__":
    raise Exception("This script is a plugin for xsconsole and cannot run independently")
    
from XSConsoleStandard import *

class VMUtils:
    operationNames = {
                      
        'start' : Struct(name = Lang("Start"), priority = 10),
        'start_on' : Struct(name = Lang("Start On This Host"), priority = 20),
        'suspend' : Struct(name = Lang("Suspend"), priority = 30),
        'resume' : Struct(name = Lang("Resume"), priority = 40),
        'clean_reboot' : Struct(name = Lang("Reboot"), priority = 50),
        'clean_shutdown' : Struct(name = Lang("Shut Down"), priority = 60),
        'hard_reboot' : Struct(name = Lang("Force Reboot"), priority = 70),
        'hard_shutdown' : Struct(name = Lang("Force Shutdown"), priority = 80),
        'none' : Struct(name = Lang("No Operation"), priority = 90)
    }
    @classmethod
    def AllowedOperations(cls):
        return cls.operationNames.keys()
        
    @classmethod
    def AsyncOperation(cls, inVMHandle, inOperation):
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
        elif inOperation == 'clean_shutdown':
            task = Task.New(lambda x: x.xenapi.Async.VM.clean_shutdown(inVMHandle.OpaqueRef()))
        elif inOperation == 'start':
            task = Task.New(lambda x: x.xenapi.Async.VM.start(inVMHandle.OpaqueRef(), False, True))
        elif inOperation == 'start_on':
            hostRef = HotAccessor().local_host.opaque_ref()
            task = Task.New(lambda x: x.xenapi.Async.VM.start_on(inVMHandle.OpaqueRef(), hostRef.OpaqueRef(), False, True))
        elif inOperation == 'suspend':
            task = Task.New(lambda x: x.xenapi.Async.VM.suspend(inVMHandle.OpaqueRef()))
        else:
            raise Exception("Unknown VM operation "+str(inOperation))
        
        return task
        
    @classmethod
    def DoOperation(cls, inVMHandle, inOperation):
        task = cls.AsyncOperation(inVMHandle, inOperation)
        
        while task is not None and task.IsPending():
            time.sleep(1)

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

class VMControlDialogue(Dialogue):
    def __init__(self, inVMHandle):
        self.vmHandle = inVMHandle
        Dialogue.__init__(self)
        self.operation = 'none'
        
        vm = HotAccessor().guest_vm[self.vmHandle]
        allowedOps = vm.allowed_operations()

        choiceList = [ name for name in allowedOps if name in VMUtils.AllowedOperations() ]
        if len(choiceList) == 0:
            choiceList.append('none')
        
        choiceList.sort(lambda x, y: cmp(VMUtils.OperationPriority(x), VMUtils.OperationPriority(y)))
        
        self.controlMenu = Menu()
        for choice in choiceList:
            self.controlMenu.AddChoice(name = VMUtils.OperationName(choice),
                onAction = self.HandleControlChoice,
                handle = choice)
            
        self.ChangeState('INITIAL')
        
    def BuildPane(self):
        pane = self.NewPane(DialoguePane(self.parent))
        pane.TitleSet(Lang("Virtual Machine Control"))
        pane.AddBox()
        
    def UpdateFieldsINITIAL(self):
        pane = self.Pane()
        pane.ResetFields()

        vm = HotAccessor().guest_vm[self.vmHandle]
        vmName = vm.name_label(None)
        if vmName is None:
            pane.AddTitleField(Lang("The Virtual Machine is no longer present"))
        else:
            pane.AddTitleField(vmName+Lang(" is ")+Lang(vm.power_state('<Unknown Power State>'))+'.')
        pane.AddMenuField(self.controlMenu)
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
    
    def UpdateFieldsCONFIRM(self):
        pane = self.Pane()
        pane.ResetFields()

        vm = HotAccessor().guest_vm[self.vmHandle]
        vmName = vm.name_label(None)
        if vmName is None:
            pane.AddTitleField(Lang("The Virtual Machine is no longer present"))
        else:
            pane.AddTitleField(Lang('Press <F8> to confirm this operation'))
            pane.AddStatusField(Lang("Operation", 20), VMUtils.OperationName(self.operation))
            pane.AddStatusField(Lang("Virtual Machine", 20), vmName)

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
        self.ChangeState('CONFIRM')
        
    def Commit(self):
        Layout.Inst().PopDialogue()

        operationName = VMUtils.OperationName(self.operation)
        vmName = HotAccessor().guest_vm[self.vmHandle].name_label(Lang('<Unknown>'))
        messagePrefix = operationName + Lang(' operation on ') + vmName + ' '
        try:
            task = VMUtils.AsyncOperation(self.vmHandle, self.operation)
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
