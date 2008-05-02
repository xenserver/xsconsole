# Copyright (c) Citrix Systems 2008. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

if __name__ == "__main__":
    raise Exception("This script is a plugin for xsconsole and cannot run independently")
    
from XSConsoleStandard import *

class HostEvacuateUtils:
    @classmethod
    def EnableHost(cls, inHost):
        Task.Sync(lambda x: x.xenapi.host.enable(inHost.OpaqueRef()))

    @classmethod
    def DesignateNewMaster(cls, inHost):
        Task.Sync(lambda x: x.xenapi.pool.designate_new_master(inHost.OpaqueRef()))
        
class HostEvacuateDialogue(Dialogue):
    def __init__(self):
        Dialogue.__init__(self)
        db = HotAccessor()
        self.newMaster = None
        self.hostWasEnabled = db.local_host.enabled(False)
        if self.hostWasEnabled and db.local_pool.master.uuid() == db.local_host.uuid():
            # We are the pool master
            self.ChangeState('CHOOSEMASTER')
        else:
            self.ChangeState('CONFIRM')
    
    def BuildPaneCHOOSEMASTER(self):
        self.hostMenu = Menu()
        hostList = {}
        for host in HotAccessor().host:
            # Make sortable by name, but keep hosts with identical names by appending uuid. User never sees the dict keys
            hostList[host.name_label()+host.uuid()] = host

        self.hostMenu = Menu()
        for hostName in sorted(hostList.keys()):
            host = hostList[hostName]
            if host.uuid() != HotAccessor().local_host.uuid():
                self.hostMenu.AddChoice(name = host.name_label(),
                    onAction = self.HandleHostChoice,
                    handle = host)
                    
        if self.hostMenu.NumChoices() == 0:
            self.hostMenu.AddChoice(name = Lang('<No hosts available>'))

    def BuildPane(self):
        pane = self.NewPane(DialoguePane(self.parent))
        pane.ResetPosition()
        pane.TitleSet(Lang("Maintenance Mode"))
        pane.AddBox()
        if hasattr(self, 'BuildPane'+self.state):
            handled = getattr(self, 'BuildPane'+self.state)() # Despatch method named 'BuildPane'+self.state

    def UpdateFieldsCHOOSEMASTER(self):
        pane = self.Pane()
        pane.ResetFields()

        pane.AddWrappedBoldTextField(Lang("This host is the Pool Master.  To enable this host to enter Maintenance Mode, please nominate a new Master for this Pool."))
        pane.NewLine()
        pane.AddMenuField(self.hostMenu)
        
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
    
    def UpdateFieldsCONFIRM(self):
        pane = self.Pane()
        pane.ResetFields()

        if self.hostWasEnabled:

            pane.AddTitleField(Lang("Press <F8> to confirm the following actions."))
            numVMs = max(0, len(HotAccessor().local_host.resident_VMs([]))-1) # Subtract 1 for dom0
            pane.AddWrappedTextField(Lang('1.  Prevent new VMs starting on or migrating to this host'))
            pane.AddWrappedTextField(Lang('2.  Migrate ') + str(numVMs) + Language.Quantity(' Virtual Machine', numVMs) +
                Lang(' to other hosts'))
            
            if self.newMaster is not None:
                pane.AddWrappedTextField(Lang('3.  Designate host ') + self.newMaster.name_label(Lang('<Unknown>')) +
                    Lang(' as the new Pool Master'))
        else:
            pane.AddWrappedBoldTextField(Lang('Press <F8> to exit Maintenance Mode and return this host to normal operation'))

        pane.AddKeyHelpField( { Lang("<F8>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
    
    def UpdateFields(self):
        self.Pane().ResetPosition()
        getattr(self, 'UpdateFields'+self.state)() # Despatch method named 'UpdateFields'+self.state

    def ChangeState(self, inState):
        self.state = inState
        self.BuildPane()
        self.UpdateFields()
    
    def HandleKeyCHOOSEMASTER(self, inKey):
        return self.hostMenu.HandleKey(inKey)

    def HandleKeyCONFIRM(self, inKey):
        if inKey == 'KEY_F(8)':
            self.Commit()

    def HandleKey(self,  inKey):
        handled = False
        if hasattr(self, 'HandleKey'+self.state):
            handled = getattr(self, 'HandleKey'+self.state)(inKey)
        
        if not handled and inKey == 'KEY_ESCAPE':
            Layout.Inst().PopDialogue()
            handled = True

        return handled

    def HandleHostChoice(self, inChoice):
        self.newMaster = inChoice
        self.ChangeState('CONFIRM')

    def Commit(self):
        Layout.Inst().PopDialogue()

        if self.hostWasEnabled:
            try:
                Layout.Inst().TransientBanner(Lang('Entering Maintenance Mode...'))
                time.sleep(0.5) # Prevent flicker when host has no VMs and command completes quickly
                ShellPipe(['xe', 'host-evacuate', 'uuid='+HotAccessor().local_host.uuid()]).Call()

                message = None
                if self.newMaster is not None:
                    Layout.Inst().TransientBanner(Lang('Designating New Pool Master...'))
                    HostEvacuateUtils.DesignateNewMaster(self.newMaster.HotOpaqueRef())
                    
                    message = Lang('Please allow several seconds for the pool to propagate information about the new Master')
                Layout.Inst().PushDialogue(InfoDialogue(Lang("Host Successfully Entered Maintenance Mode"), message))
            except Exception, e:
                Layout.Inst().PushDialogue(InfoDialogue(Lang("Enter Maintenance Mode Failed To Complete"), Lang(e)))
        else:
            try:
                HostEvacuateUtils.EnableHost(HotAccessor().local_host_ref())
                Layout.Inst().PushDialogue(InfoDialogue(Lang("Host Successfully Exited Maintenance Mode")))
            except Exception, e:
                Layout.Inst().PushDialogue(InfoDialogue(Lang("Exit Maintenance Mode Failed"), Lang(e)))
            
class XSFeatureHostEvacuate:
    @classmethod
    def StatusUpdateHandler(cls, inPane):
        db = HotAccessor()
        inPane.AddTitleField("Maintenance Mode")
        if db.local_host.enabled():
            
            inPane.AddWrappedTextField(Lang('Entering Maintenance Mode will migrate all Virtual Machines running on this host '
                'to other hosts in the Resource Pool.  It is typically used before shutting down a host for maintenance, '
                'and is only relevant for hosts in Resource Pools.'))
            inPane.NewLine()
            
            if db.host(None) is None:
                pass # Info not available, so print nothing
            elif len(db.host([])) <= 1:
                inPane.AddWrappedTextField(Lang('This host is not in a Resource Pool, so this option is disabled.'))
                inPane.NewLine()
            elif db.local_pool.master.uuid() == db.local_host.uuid():
                inPane.AddWrappedTextField(Lang('This host is the Pool Master, so it will be necessary to nominate a new Pool '
                    'Master as part of this operation.'))
                inPane.NewLine()

            if len(db.host([])) > 1:
                inPane.AddKeyHelpField( { Lang("<Enter>") : Lang("Evacuate Host") } )
        else:
            inPane.AddWrappedTextField(Lang('This host is already in Maintenance Mode.  Press <Enter> to '
                'exit Maintenance Mode and return to normal operation.  This operation will not automatically migrate '
                'Virtual Machines back to this host or reassign the Pool Master, but these can be done manually.'))
    
    @classmethod
    def ActivateHandler(cls):
        DialogueUtils.AuthenticatedOnly(lambda: Layout.Inst().PushDialogue(HostEvacuateDialogue()))
    
    def Register(self):
        Importer.RegisterNamedPlugIn(
            self,
            'HOST_EVACUATE', # Key of this plugin for replacement, etc.
            {
                'menuname' : 'MENU_VM',
                'menupriority' : 400,
                'menutext' : Lang('Enter/Exit Maintenance Mode') ,
                'activatehandler' : XSFeatureHostEvacuate.ActivateHandler,
                'statusupdatehandler' : XSFeatureHostEvacuate.StatusUpdateHandler
            }
        )

        Importer.RegisterResource(
            self,
            'HOST_EVACUATE', # Name of this item for replacement, etc.
            {
                'HostEvacuateUtils' : HostEvacuateUtils
            }
        )

# Register this plugin when module is imported
XSFeatureHostEvacuate().Register()
