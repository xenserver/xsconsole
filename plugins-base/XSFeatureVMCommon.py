# Copyright (c) Citrix Systems 2008. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

if __name__ == "__main__":
    raise Exception("This script is a plugin for xsconsole and cannot run independently")
    
from XSConsoleStandard import *

class VMControlDialogue(Dialogue):
    def __init__(self, inVMHandle):
        self.vmHandle = inVMHandle
        Dialogue.__init__(self)
        
        
        vm = HotAccessor().guest_vm(self.vmHandle)
        powerState = vm.power_state('').lower()
        if powerState.startswith('running'):
            choiceList = [
                (Lang('Shut Down'), 'SHUTDOWN'),
                (Lang('Suspend'), 'SUSPEND'),
                (Lang('Reboot'), 'REBOOT'),
                (Lang('Force Shutdown'), 'FORCESHUTDOWN'),
                (Lang('Force Reboot'), 'FORCEREBOOT')
            ]
        elif powerState.startswith('suspended'):
            choiceList = [
                (Lang('Resume'), 'RESUME'),
                (Lang('Force Shutdown'), 'FORCESHUTDOWN')
            ]
        elif powerState.startswith('halted'):
            choiceList = [
                (Lang('Start'), 'START')
            ]
        else:
            choiceList = [
                (Lang('<Unknown power state>'),'NONE')
            ]

        self.controlMenu = Menu()
        for choice in choiceList:
            self.controlMenu.AddChoice(name = choice[0],
                onAction = self.HandleControlChoice,
                handle = choice[1])
            
        self.ChangeState('INITIAL')
        
    def BuildPane(self):
        pane = self.NewPane(DialoguePane(self.parent))
        pane.TitleSet(Lang("Virtual Machine Control"))
        pane.AddBox()
        
    def UpdateFieldsINITIAL(self):
        pane = self.Pane()
        pane.ResetFields()

        vm = HotAccessor().guest_vm(self.vmHandle)
        vmName = vm.name_label(None)
        if vmName is None:
            pane.AddTitleField(Lang("The Virtual Machine is no longer present"))
        else:
            pane.AddTitleField(vmName+Lang(" is ")+Lang(vm.power_state('<Unknown Power State>'))+'.')
        pane.AddMenuField(self.controlMenu)
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
    
    def UpdateFields(self):
        self.Pane().ResetPosition()
        getattr(self, 'UpdateFields'+self.state)() # Despatch method named 'UpdateFields'+self.state

    def ChangeState(self, inState):
        self.state = inState
        self.BuildPane()
        self.UpdateFields()
    
    def HandleKeyINITIAL(self, inKey):
        return self.controlMenu.HandleKey(inKey)

    def HandleKey(self,  inKey):
        handled = False
        if hasattr(self, 'HandleKey'+self.state):
            handled = getattr(self, 'HandleKey'+self.state)(inKey)
        
        if not handled and inKey == 'KEY_ESCAPE':
            Layout.Inst().PopDialogue()
            handled = True

        return handled
    
    def HandleControlChoice(self, inChoice):
        try:
            if inChoice == 'FORCEREBOOT':
                Layout.Inst().TransientBanner(Lang("Forced Reboot In Progress..."))
                HotData.Inst().Session().xenapi.VM.hard_reboot(self.vmHandle.OpaqueRef())
            elif inChoice == 'FORCESHUTDOWN':
                Layout.Inst().TransientBanner(Lang("Forced Shutdown In Progress..."))
                HotData.Inst().Session().xenapi.VM.hard_shutdown(self.vmHandle.OpaqueRef())
            elif inChoice == 'REBOOT':
                Layout.Inst().TransientBanner(Lang("Reboot In Progress..."))
                HotData.Inst().Session().xenapi.VM.clean_reboot(self.vmHandle.OpaqueRef())
            elif inChoice == 'RESUME':
                Layout.Inst().TransientBanner(Lang("Resume In Progress..."))
                HotData.Inst().Session().xenapi.VM.resume(self.vmHandle.OpaqueRef(), False, True)
            elif inChoice == 'SHUTDOWN':
                Layout.Inst().TransientBanner(Lang("Shutdown In Progress..."))
                HotData.Inst().Session().xenapi.VM.clean_shutdown(self.vmHandle.OpaqueRef())
            elif inChoice == 'START':
                Layout.Inst().TransientBanner(Lang("Start In Progress..."))
                HotData.Inst().Session().xenapi.VM.start(self.vmHandle.OpaqueRef(), False, True)
            elif inChoice == 'SUSPEND':
                Layout.Inst().TransientBanner(Lang("Suspend In Progress..."))
                HotData.Inst().Session().xenapi.VM.suspend(self.vmHandle.OpaqueRef())

            
            Layout.Inst().PopDialogue()
            Layout.Inst().PushDialogue(InfoDialogue(Lang("Operation Successful")))
        except Exception, e:
            Layout.Inst().PushDialogue(InfoDialogue(Lang("Operation Failed"), Lang(e)))
       
    
    def Commit(self, inMessage):
        try:
            Data.Inst().SaveToResolvConf()
            Layout.Inst().PushDialogue(InfoDialogue( inMessage))
        except Exception, e:
            Layout.Inst().PushDialogue(InfoDialogue( Lang("Update failed: ")+Lang(e)))

class XSFeatureVMCommon:
    def Register(self):
        Importer.RegisterResource(
            self,
            'VM_COMMON', # Name of this item for replacement, etc.
            {
                'VMControlDialogue' : VMControlDialogue, # Name of the menu this item leads to when selected
            }
        )

# Register this plugin when module is imported
XSFeatureVMCommon().Register()
