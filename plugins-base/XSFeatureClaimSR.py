# Copyright (c) Citrix Systems 2008. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

if __name__ == "__main__":
    raise Exception("This script is a plugin for xsconsole and cannot run independently")
    
from XSConsoleStandard import *

class ClaimSRDialogue(Dialogue):
    def __init__(self):
        Dialogue.__init__(self)

        self.deviceToErase = None
        self.srName = None
        self.srSize = None
        
        self.ChangeState('INITIAL')

    def DeviceString(self, inDevice):
        retVal = "%-6.6s%-44.44s%-10.10s%10.10s" % (
            FirstValue(inDevice.bus, '')[:6],
            FirstValue(inDevice.name, '')[:44],
            FirstValue(inDevice.device, '')[:10],
            FirstValue(FileUtils.SizeString(inDevice.size), '')
        )
        return retVal
        
    def BuildPaneBase(self):
        pane = self.NewPane(DialoguePane(self.parent))
        pane.TitleSet(Lang("Claim Disk As Storage Repository"))
        pane.AddBox()
    
    def BuildPaneINITIAL(self):
        self.BuildPaneBase()
        self.UpdateFields()
        
    def BuildPaneDEVICE(self):
        self.deviceList = FileUtils.SRDeviceList()
        
        self.BuildPaneBase()
        
        choiceDefs = []
        for device in self.deviceList:
            choiceDefs.append(ChoiceDef(self.DeviceString(device), lambda: self.HandleDeviceChoice(self.deviceMenu.ChoiceIndex()) ) )
        
        if len(choiceDefs) == 0:
            choiceDefs.append(ChoiceDef(Lang("<No devices available>", 70), None))
    
        # 'Custom' manual choice disabled    
        # choiceDefs.append(ChoiceDef(Lang("Specify a device manually", 70), lambda: self.HandleDeviceChoice(None) ) )

        self.deviceMenu = Menu(self, None, Lang("Select Device"), choiceDefs)
        self.UpdateFields()

    def BuildPaneALREADYTHERE(self):
        self.BuildPaneBase()
        self.UpdateFields()

    def BuildPaneCUSTOM(self):
        self.BuildPaneBase()
        self.UpdateFields()
        
    def BuildPaneCONFIRM(self):
        self.BuildPaneBase()
        self.UpdateFields()
    
    def BuildPaneREBOOT(self):
        self.BuildPaneBase()
        self.UpdateFields()
    
    def ChangeState(self, inState):
        self.state = inState
        getattr(self, 'BuildPane'+self.state)() # Despatch method named 'BuildPane'+self.state
    
    def UpdateFields(self):
        self.Pane().ResetPosition()
        getattr(self, 'UpdateFields'+self.state)() # Despatch method named 'UpdateFields'+self.state
        
    def UpdateFieldsINITIAL(self):
        pane = self.Pane()
        pane.ResetFields()
        
        pane.AddWarningField(Lang("WARNING"))
        pane.AddWrappedTextField(Lang("Once a disk is selected, this function will erase all information on that disk.  Do you want to continue?"))
        pane.AddKeyHelpField( { Lang("<F8>") : Lang("Continue"), Lang("<Esc>") : Lang("Cancel") } )

    def UpdateFieldsDEVICE(self):
        pane = self.Pane()
        pane.ResetFields()
        
        pane.AddTitleField(Lang("Select a disk to erase and claim as a Storage Repository."))
        pane.AddMenuField(self.deviceMenu)
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel"), 
            "<F5>" : Lang("Rescan") } )

    def UpdateFieldsALREADYTHERE(self):
        pane = self.Pane()
        pane.ResetFields()
        
        pane.AddWarningField(Lang("WARNING"))
        
        pane.AddWrappedBoldTextField(Lang("A Storage Repository has already been created on this disk.  "
            "Continuing will destroy all information in this Storage Repository.  Would you like to continue?"))
        pane.NewLine()
        pane.AddStatusField(Lang("Current SR Name", 20), str(self.srName))

        pane.AddKeyHelpField( { Lang("<F8>") : Lang("Continue"), Lang("<Esc>") : Lang("Cancel") } )

    def UpdateFieldsCUSTOM(self):
        pane = self.Pane()
        pane.ResetFields()
        
        pane.AddTitleField(Lang("Enter the device name, e.g. /dev/sdb"))
        pane.AddInputField(Lang("Device Name",  16), '', 'device')
        pane.NewLine()
        pane.AddWrappedTextField(Lang("WARNING: No checks will be performed on this device before it is erased."))
        
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Exit") } )
        if pane.CurrentInput() is None:
            pane.InputIndexSet(0)
            
    def UpdateFieldsCONFIRM(self):
        pane = self.Pane()
        pane.ResetFields()
        
        pane.AddWrappedBoldTextField(Lang("Press <F8> to confirm that you want to erase all information on this disk and use it as a Storage Repository.  Data currently on this disk cannot be recovered after this step."))
        pane.NewLine()
        pane.AddWrappedBoldTextField(Lang("Device"))
        if isinstance(self.deviceToErase, Struct):
            pane.AddWrappedTextField(self.DeviceString(self.deviceToErase))
        else:
            pane.AddWrappedTextField(str(self.deviceToErase))

        pane.AddKeyHelpField( { Lang("<F8>") : Lang("Erase and Claim"), Lang("<Esc>") : Lang("Cancel") } )

    def UpdateFieldsREBOOT(self):
        pane = self.Pane()
        pane.ResetFields()
        
        pane.AddWrappedBoldTextField(Lang("This server needs to reboot to use the new Storage Repository.  Press <F8> to reboot now."))

        pane.AddKeyHelpField( { Lang("<F8>") : Lang("Reboot"), Lang("<Esc>") : Lang("Cancel") } )

    def HandleKey(self, inKey):
        handled = False
        if hasattr(self, 'HandleKey'+self.state):
            handled = getattr(self, 'HandleKey'+self.state)(inKey)
        
        if not handled and inKey == 'KEY_ESCAPE':
            Layout.Inst().PopDialogue()
            handled = True

        return handled
        
    def HandleKeyINITIAL(self, inKey):
        handled = False
        
        if inKey == 'KEY_F(8)':
            Layout.Inst().TransientBanner(Lang("Scanning..."))
            Data.Inst().Update() # Get current SR list
            self.ChangeState('DEVICE')
            handled = True
            
        return handled

    def HandleKeyDEVICE(self, inKey):
        handled = self.deviceMenu.HandleKey(inKey)
        
        if not handled and inKey == 'KEY_F(5)':
            Layout.Inst().PushDialogue(BannerDialogue( Lang("Rescanning...")))
            Layout.Inst().Refresh()
            Layout.Inst().DoUpdate()
            Layout.Inst().PopDialogue()
            self.BuildPaneDEVICE() # Updates self.deviceList
            time.sleep(0.5) # Display rescanning box for a reasonable time
            Layout.Inst().Refresh()
            handled = True
            
        return handled

    def HandleKeyALREADYTHERE(self, inKey):
        handled = False
        
        if inKey == 'KEY_F(8)':
            self.ChangeState('CONFIRM')
            handled = True
            
        return handled

    def HandleKeyCUSTOM(self, inKey):
        handled = True
        pane = self.Pane()
        if pane.CurrentInput() is None:
            pane.InputIndexSet(0)
        if inKey == 'KEY_ENTER':
            inputValues = pane.GetFieldValues()
            self.deviceToErase = Struct(device = inputValues['device'])
            self.ChangeState('CONFIRM')
        elif pane.CurrentInput().HandleKey(inKey):
            pass # Leave handled as True
        else:
            handled = False
        return handled
        
    def HandleKeyCONFIRM(self, inKey):
        handled = False
        
        if inKey == 'KEY_F(8)':
            self.DoAction()
            handled = True
            
        return handled
    
    def HandleKeyREBOOT(self, inKey):
        handled = False
        
        if inKey == 'KEY_F(8)':
            Layout.Inst().ExitBannerSet(Lang("Rebooting..."))
            Layout.Inst().ExitCommandSet('/sbin/shutdown -r now')
            handled = True
            
        return handled
    
    def HandleDeviceChoice(self, inChoice):
        if inChoice is None:
            self.ChangeState('CUSTOM')
        else:
            self.deviceToErase = self.deviceList[inChoice]
            if self.IsKnownSROnDisk(self.deviceToErase.device):
                self.ChangeState('ALREADYTHERE')
            else:
                self.ChangeState('CONFIRM')

    def IsKnownSROnDisk(self, inDevice):
        retVal = False
        for pbd in Data.Inst().host.PBDs([]):
            device = pbd.get('device_config', {}).get('device', '')
            match = re.match(r'([^0-9]+)[0-9]*$', device)
            if match: # Remove trailing partition numbers
                device = match.group(1)
            if device == inDevice:
                # This is the PBD we want to claim.  Does it have an SR?
                srName = pbd.get('SR', {}).get('name_label', None)
                if srName is not None:
                    self.srName = srName
                    self.srSize = int(pbd.get('SR', {}).get('physical_size', 0))
                    retVal = True
        return retVal

    def DoAction(self):
        Layout.Inst().TransientBanner(Lang("Claiming and Configuring Disk..."))

        status, output = commands.getstatusoutput(
            "/opt/xensource/libexec/delete-partitions-and-claim-disk "+self.deviceToErase.device+" 2>&1")
        
        time.sleep(4) # Allow xapi to pick up the new SR
        Data.Inst().Update() # Read information about the new SR
        
        if status != 0:
            Layout.Inst().PopDialogue()
            Layout.Inst().PushDialogue(InfoDialogue(Lang("Disk Claim Failed"), output))
        else:
            try:
                Data.Inst().SetPoolSRsFromDeviceIfNotSet(self.deviceToErase.device)
            except Exception, e:
                Layout.Inst().PushDialogue(InfoDialogue(Lang("Disk Claimed, but could not set as default SR: ") + Lang(e)))
                # Continue to reboot dialogue
            self.ChangeState('REBOOT')

class XSFeatureClaimSR:
    @classmethod
    def StatusUpdateHandler(cls, inPane):
        data = Data.Inst()
        inPane.AddTitleField(Lang("Claim Local Disk as SR"))
    
        inPane.AddWrappedTextField(Lang("Local disks can be configured as Storage Repositories "
            "for use by virtual machines.  Press <Enter> to list the disks available."))

        inPane.AddKeyHelpField( {
            Lang("<Enter>") : Lang("Claim Disk as SRs")
        })

    @classmethod
    def ActivateHandler(cls):
        DialogueUtils.AuthenticatedOnly(lambda: Layout.Inst().PushDialogue(ClaimSRDialogue()))
        
    def Register(self):
        Importer.RegisterNamedPlugIn(
            self,
            'CLAIM_SR', # Key of this plugin for replacement, etc.
            {
                'menuname' : 'MENU_DISK',
                'menupriority' : 500,
                'menutext' : Lang('Claim Local Disk as SR') ,
                'statusupdatehandler' : self.StatusUpdateHandler,
                'activatehandler' : self.ActivateHandler
            }
        )

# Register this plugin when module is imported
XSFeatureClaimSR().Register()
