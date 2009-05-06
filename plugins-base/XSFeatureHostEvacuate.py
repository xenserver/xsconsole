# Copyright (c) Citrix Systems 2008. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

if __name__ == "__main__":
    raise Exception("This script is a plugin for xsconsole and cannot run independently")
    
from XSConsoleStandard import *

class HostEvacuateDialogue(Dialogue):
    def __init__(self):
        Dialogue.__init__(self)
        db = HotAccessor()
        self.newMaster = None
        self.hostWasEnabled = db.local_host.enabled(False)
        self.migrateMenu = Menu()
        self.migrateMenu.AddChoice(name = Lang('Migrate, Resume or Restart Virtual Machines on This Host'),
            onAction = self.HandleMigrateChoice,
            handle = 'YES')
        self.migrateMenu.AddChoice(name = Lang('Do Not Alter Virtual Machines'),
            onAction = self.HandleMigrateChoice,
            handle = 'NO')
        
        if self.hostWasEnabled:
            if db.local_pool.master.uuid() == db.local_host.uuid():
                # We are the pool master
                if len(db.host([])) == 1:
                    # This is a pool of one
                    self.ChangeState('CONFIRM')
                else:
                    # Host is master of a pool of more than one host
                    self.ChangeState('CHOOSEMASTER')
            else:
                # Host is a slave
                self.ChangeState('CONFIRM')
        else:
            evacuatedConfig = db.local_host.other_config({}).get('MAINTENANCE_MODE_EVACUATED_VMS', '')
            if evacuatedConfig != '':
                self.evacuatedVMs = [ HotOpaqueRef(opaqueRef, 'vm') for opaqueRef in evacuatedConfig.split(',') ]
                self.ChangeState('MIGRATEBACK')
            else:
                self.evacuatedVMs = []
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
        
        pane.AddKeyHelpField( { Lang("<Up/Down>") : Lang("Select"), Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
    
    
    def UpdateFieldsMIGRATEBACK(self):
        pane = self.Pane()
        pane.ResetFields()
        
        pane.AddTitleField(Lang('The following were running on this host when it entered Maintenance Mode.  Would you like reinstate them on this host?'))
        for i, vmRef in enumerate(self.evacuatedVMs):
            if i > 4:
                pane.AddWrappedTextField(Lang('...and others'))
                break
            pane.AddWrappedTextField(HotAccessor().vm[vmRef].name_label(Lang('<Unknown>')))

        
        pane.NewLine()
        pane.AddMenuField(self.migrateMenu)
        pane.AddKeyHelpField( { Lang("<Up/Down>") : Lang("Select"), Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
    
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
    
    def HandleKeyMIGRATEBACK(self, inKey):
        return self.migrateMenu.HandleKey(inKey)

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

    def HandleMigrateChoice(self, inChoice):
        if inChoice != 'YES':
            # Clear evacuated VM list
            self.evacuatedVMs = []
        self.ChangeState('CONFIRM')

    def Commit(self):
        hostUtils = Importer.GetResource('HostUtils')
        Layout.Inst().PopDialogue()

        if self.hostWasEnabled:
            try:
                Layout.Inst().TransientBanner(Lang('Entering Maintenance Mode...'))
                hostUtils.DoOperation('disable', HotAccessor().local_host_ref())
                hostUtils.DoOperation('evacuate', HotAccessor().local_host_ref())
                message = None
                if self.newMaster is not None:
                    Layout.Inst().TransientBanner(Lang('Designating New Pool Master...'))
                    hostUtils.DoOperation('designate_new_master', self.newMaster.HotOpaqueRef())
                    
                    message = Lang('Please allow several seconds for the pool to propagate information about the new Master')
                Layout.Inst().PushDialogue(InfoDialogue(Lang("Host Successfully Entered Maintenance Mode"), message))
            except Exception, e:
                Layout.Inst().PushDialogue(InfoDialogue(Lang("Enter Maintenance Mode Failed to Complete"), Lang(e)))
        else:
            try:
                Layout.Inst().TransientBanner(Lang('Exiting Maintenance Mode...'))
                hostUtils.DoOperation('enable', HotAccessor().local_host_ref())
                vmUtils = Importer.GetResource('VMUtils')
                vmUtils.ReinstateVMs(HotAccessor().local_host_ref(), self.evacuatedVMs)
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
                'to other hosts in the Resource Pool.  It is used before shutting down a host for maintenance.'))
            inPane.NewLine()
            
            if db.host(None) is None:
                pass # Info not available, so print nothing
            elif len(db.host([])) > 1 and db.local_pool.master.uuid() == db.local_host.uuid():
                inPane.AddWrappedTextField(Lang('This host is the Pool Master, so it will be necessary to nominate a new Pool '
                    'Master as part of this operation.'))
                inPane.NewLine()


            inPane.AddKeyHelpField( { Lang("<Enter>") : Lang("Evacuate Host") } )
        else:
            inPane.AddWrappedTextField(Lang('This host is already in Maintenance Mode.  Press <Enter> to '
                'exit Maintenance Mode and return to normal operation.'))
    
    @classmethod
    def ActivateHandler(cls):
        db=HotAccessor()
        if len(db.host([])) == 1 and len(db.local_host.resident_VMs([])) > 1: # If we are in a pool of one and VMs are running
            Layout.Inst().PushDialogue(InfoDialogue(Lang('This host has running Virtual Machines.  Please suspend or shutdown the Virtual Machines before entering Maintenance Mode.')))
        else:
            DialogueUtils.AuthenticatedOnly(lambda: Layout.Inst().PushDialogue(HostEvacuateDialogue()))
    
    def Register(self):
        Importer.RegisterNamedPlugIn(
            self,
            'HOST_EVACUATE', # Key of this plugin for replacement, etc.
            {
                'menuname' : 'MENU_REBOOTSHUTDOWN',
                'menupriority' : 100,
                'menutext' : Lang('Enter/Exit Maintenance Mode') ,
                'activatehandler' : XSFeatureHostEvacuate.ActivateHandler,
                'statusupdatehandler' : XSFeatureHostEvacuate.StatusUpdateHandler
            }
        )

# Register this plugin when module is imported
XSFeatureHostEvacuate().Register()
