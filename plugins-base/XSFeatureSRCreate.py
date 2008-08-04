# Copyright (c) Citrix Systems 2008. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

if __name__ == "__main__":
    raise Exception("This script is a plugin for xsconsole and cannot run independently")
    
from XSConsoleStandard import *
import xml.dom.minidom

class SRNewDialogue(Dialogue):
    srTypeNames = {
        'NFS': Lang('NFS Storage'),
        'ISCSI': Lang('iSCSI Storage'),
        'NETAPP': Lang('NetApp'),
        'HBA': Lang('Hardware HBA (Fibre Channel)'),
        'EQUAL': Lang('Dell EqualLogic'),
        'CIFS_ISO': Lang('Windows File Sharing (CIFS) ISO Library'),
        'NFS_ISO': Lang('NFS ISO Library')
    }    
    
    netAppProvisioning = {
        'THICK' : Struct(name=Lang('Thick Provisioning'), config={'allocation':'thick'}),
        'THIN_NO_ASIS' :  Struct(name=Lang('Thin Provisioning Without A-SIS Deduplication'), config={'allocation':'thin','asis':'false'}),
        'THIN_ASIS' : Struct(name=Lang('Thin Provisioning With A-SIS Deduplication'), config={'allocation':'thin', 'asis':'true'})
    }
    
    def NetAppProvisioningName(self, inType):
        return self.netAppProvisioning[inType].name
        
    def NetAppProvisioningConfig(self, inType):
        return self.netAppProvisioning[inType].config
    
    def __init__(self, inVariant):

        Dialogue.__init__(self)
        self.variant = inVariant
        self.srParams = {}
        self.createMenu = Menu()

        if self.variant == 'CREATE':
            choices = ['NFS', 'ISCSI', 'NETAPP', 'HBA', 'EQUAL']
        else: # ATTACH choices
            choices = ['NFS',  'ISCSI', 'NETAPP', 'HBA', 'EQUAL', 'CIFS_ISO', 'NFS_ISO']
        
        for type in choices:
            self.createMenu.AddChoice(name = self.srTypeNames[type],
                onAction = self.HandleCreateChoice,
                handle = type)

        self.ChangeState('INITIAL')
    
    def IQNString(self, inIQN, inLUN = None):
        if inLUN is None: # LUN not present
            retVal = "TGPT %-4.4s %-60.60s" % (inIQN.tgpt[:4], inIQN.name[:60])
        else:
            retVal = "TGPT %-4.4s %-52.52s LUN %-3.3s" % (inIQN.tgpt[:4], inIQN.name[:52], str(inLUN)[:3])
        
        return retVal
        
    def LUNString(self, inLUN):
        retVal = "LUN %-4.4s %s" % (inLUN.LUNid[:4], (SizeUtils.SRSizeString(inLUN.size)+ ' ('+inLUN.vendor)[:62]+')')
        
        return retVal
        
    def AggregateString(self, inAggregate):
        retVal = "%-60.60s %-9.9s" % (inAggregate.name[:60], (SizeUtils.SRSizeString(inAggregate.size))[:9])
        return retVal
        
    def NetAppSRString(self, inNetAppSR):
        retVal = "%-36.36s  %-22.22s %-9.9s" % (self.ExtendedSRName(inNetAppSR.uuid)[:36], inNetAppSR.aggregate[:22], (SizeUtils.SRSizeString(inNetAppSR.size))[:9])
        return retVal

    def DeviceString(self, inDevice):
        idLen=72
        idPrefix = inDevice.vendor[:10]+' ' + ('%7s' % SizeUtils.SRSizeString(inDevice.size)) + ' '
        idString = idPrefix + inDevice.serial + '  ' + inDevice.path
        if len(idString) > idLen:
            idString = idPrefix + inDevice.serial + '  ' + inDevice.path[:5]+'...'
            spaceLeft = idLen - len(idString)
            if spaceLeft > 0:
                idString += inDevice.path[-spaceLeft:]
        retVal = idString[:72]
        return retVal
        
    def EqualSizeStr(self, inSize):
        if re.match(r'.*B$', inSize):
            retVal = inSize
        else:
            retVal = SizeUtils.SRSizeString(inSize)
        return retVal
        
    def StoragePoolString(self, inStoragePool):
        retVal = "%-39.39s %32.32s" % (inStoragePool.name[:39], (self.EqualSizeStr(inStoragePool.capacity))[:12] + (' ('+self.EqualSizeStr(inStoragePool.freespace)[:12]+Lang(' free)'))[:32])
        return retVal
    
    def EqualSRString(self, inSR):
        retVal = "%-56.56s %-12.12s" % (self.ExtendedSRName(inSR.uuid)[:56], (SizeUtils.SRSizeString(inSR.size))[:12])
        return retVal
        
    def ExtendedSRName(self, inUUID):
        retVal = inUUID
        matchingSRs = [ sr for sr in HotAccessor().sr if sr.uuid() == inUUID ]
        if len(matchingSRs) > 0:
            sr = matchingSRs[0]
            retVal = sr.name_label(Lang('<Unknown>'))
            if len(sr.PBDs()) == 0:
                retVal += Lang(' (detached)')
        return retVal

    def BuildPanePROBE_NFS(self):
        self.srMenu = Menu()
        names = {}
        for sr in HotAccessor().sr:
            names[sr.uuid()] = sr.name_label(Lang('<Unknown>'))
            if len(sr.PBDs()) == 0:
                names[sr.uuid()] += Lang(' (detached)')
            
        for srChoice in self.srChoices:
            self.srMenu.AddChoice(name = self.ExtendedSRName(srChoice),
                onAction = self.HandleProbeChoice,
                handle = srChoice)
        if self.srMenu.NumChoices() == 0:
            self.srMenu.AddChoice(name = Lang('<No Storage Repositories Detected>'))
            
    def BuildPanePROBE_ISCSI_IQN(self):
        self.iqnMenu = Menu()
        for iqnChoice in self.iqnChoices:
            self.iqnMenu.AddChoice(name = self.IQNString(iqnChoice),
                onAction = self.HandleIQNChoice,
                handle = iqnChoice)
        if self.iqnMenu.NumChoices() == 0:
            self.iqnMenu.AddChoice(name = Lang('<No IQNs Detected>'))
    
    def BuildPanePROBE_ISCSI_LUN(self):
        self.lunMenu = Menu()
        for lunChoice in self.lunChoices:
            self.lunMenu.AddChoice(name = self.LUNString(lunChoice),
                onAction = self.HandleLUNChoice,
                handle = lunChoice)
        if self.lunMenu.NumChoices() == 0:
            self.lunMenu.AddChoice(name = Lang('<No LUNs Detected>'))
            
    def BuildPanePROBE_ISCSI_SR(self):
        self.srMenu = Menu()
        for srChoice in self.srChoices:
            self.srMenu.AddChoice(name = self.ExtendedSRName(srChoice),
                onAction = self.HandleiSCSISRChoice,
                handle = srChoice)
        if self.srMenu.NumChoices() == 0:
            self.srMenu.AddChoice(name = Lang('<No Storage Repositories Detected>'))

    def BuildPanePROBE_NETAPP_AGGREGATE(self):
        self.aggregateMenu = Menu()
        for aggregateChoice in self.aggregateChoices:
            self.aggregateMenu.AddChoice(name = self.AggregateString(aggregateChoice),
                onAction = self.HandleAggregateChoice,
                handle = aggregateChoice)
        if self.aggregateMenu.NumChoices() == 0:
            self.aggregateMenu.AddChoice(name = Lang('<No Aggregates Detected>'))

    def BuildPanePROBE_NETAPP_PROVISIONING(self):
        self.provisioningMenu = Menu()

        self.provisioningMenu.AddChoice(name = self.NetAppProvisioningName('THICK'),
            onAction = self.HandleProvisioningChoice,
            handle = 'THICK')

        self.provisioningMenu.AddChoice(name = self.NetAppProvisioningName('THIN_NO_ASIS'),
            onAction = self.HandleProvisioningChoice,
            handle = 'THIN_NO_ASIS')

        if self.srParams['aggregate'].asisdedup.lower().startswith('true'):
            self.provisioningMenu.AddChoice(name = self.NetAppProvisioningName('THIN_ASIS'),
                onAction = self.HandleProvisioningChoice,
                handle = 'THIN_ASIS')
        else:
            self.provisioningMenu.AddChoice(name = Lang('<This Aggregate Does Not Support A-SIS Deduplication>'))

    def BuildPanePROBE_NETAPP_SR(self):
        self.srMenu = Menu()
        for srChoice in self.netAppSRChoices:
            self.srMenu.AddChoice(name = self.NetAppSRString(srChoice),
                onAction = self.HandleNetAppSRChoice,
                handle = srChoice)
        if self.srMenu.NumChoices() == 0:
            self.srMenu.AddChoice(name = Lang('<No Storage Repositories Detected>'))

    def BuildPanePROBE_HBA_DEVICE(self):
        self.deviceMenu = Menu()
        for deviceChoice in self.deviceChoices:
            self.deviceMenu.AddChoice(name = self.DeviceString(deviceChoice),
                onAction = self.HandleDeviceChoice,
                handle = deviceChoice)
        if self.deviceMenu.NumChoices() == 0:
            self.deviceMenu.AddChoice(name = Lang('<No Devices Detected>'))

    def BuildPanePROBE_HBA_SR(self):
        self.srMenu = Menu()
        for srChoice in self.srChoices:
            self.srMenu.AddChoice(name = self.ExtendedSRName(srChoice),
                onAction = self.HandleHBASRChoice,
                handle = srChoice)
        if self.srMenu.NumChoices() == 0:
            self.srMenu.AddChoice(name = Lang('<No Storage Repositories Detected>'))

    def BuildPanePROBE_EQUAL_STORAGEPOOL(self):
        self.storagePoolMenu = Menu()
        for storagePoolChoice in self.storagePoolChoices:
            self.storagePoolMenu.AddChoice(name = self.StoragePoolString(storagePoolChoice),
                onAction = self.HandleStoragePoolChoice,
                handle = storagePoolChoice)
        if self.storagePoolMenu.NumChoices() == 0:
            self.storagePoolMenu.AddChoice(name = Lang('<No Storage Pools Detected>'))

    def BuildPanePROBE_EQUAL_SR(self):
        self.srMenu = Menu()
        for srChoice in self.equalSRChoices:
            self.srMenu.AddChoice(name = self.EqualSRString(srChoice),
                onAction = self.HandleEqualSRChoice,
                handle = srChoice)
        if self.srMenu.NumChoices() == 0:
            self.srMenu.AddChoice(name = Lang('<No Storage Repositories Detected>'))

    def BuildPane(self):
        pane = self.NewPane(DialoguePane(self.parent))
        pane.TitleSet(Lang("New Storage Repository"))
        pane.AddBox()
        if hasattr(self, 'BuildPane'+self.state):
            handled = getattr(self, 'BuildPane'+self.state)() # Despatch method named 'BuildPane'+self.state
            
    def UpdateFieldsINITIAL(self):
        pane = self.Pane()
        pane.ResetFields()
        pane.AddTitleField(Lang('Please select the type of Storage Repository to ')+Lang(self.variant.lower()))
        pane.AddMenuField(self.createMenu)
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
    
    def UpdateFieldsGATHER_NFS(self):
        pane = self.Pane()
        pane.ResetFields()
        pane.AddTitleField(Lang('Please enter a name and path for the NFS Storage Repository'))
        pane.AddInputField(Lang('Name', 16), self.srParams.get('name', Lang('NFS virtual disk storage')), 'name')
        pane.AddInputField(Lang('Description', 16), '', 'description')
        pane.AddInputField(Lang('Share Name', 16), self.srParams.get('sharename', 'server:/path'), 'sharename')
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
        if pane.CurrentInput() is None:
            pane.InputIndexSet(0)
    
    def UpdateFieldsGATHER_NFS_ISO(self):
        pane = self.Pane()
        pane.ResetFields()
        pane.AddTitleField(Lang('Please enter a name and path for the NFS ISO Library'))
        pane.AddInputField(Lang('Name', 20), self.srParams.get('name', Lang('NFS ISO Library')), 'name')
        pane.AddInputField(Lang('Description', 20), '', 'description')
        pane.AddInputField(Lang('Share Name', 20), self.srParams.get('sharename', 'server:/path'), 'sharename')
        pane.AddInputField(Lang('Advanced Options', 20), '', 'options')
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
        if pane.CurrentInput() is None:
            pane.InputIndexSet(0)
    
    def UpdateFieldsGATHER_CIFS_ISO(self):
        pane = self.Pane()
        pane.ResetFields()
        pane.AddTitleField(Lang('Please enter a name and path for the CIFS ISO Library.  Leave the Username/Password fields blank if not required.'))
        pane.AddInputField(Lang('Name', 20), self.srParams.get('name', Lang('CIFS ISO Library')), 'name')
        pane.AddInputField(Lang('Description', 20), '', 'description')
        pane.AddInputField(Lang('Share Name', 20), self.srParams.get('sharename', '\\\\server\\sharename'), 'sharename')
        pane.AddInputField(Lang('Username', 20), '', 'username')
        pane.AddPasswordField(Lang('Password', 20), '', 'cifspassword')
        pane.AddInputField(Lang('Advanced Options', 20), '', 'options')
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
        if pane.CurrentInput() is None:
            pane.InputIndexSet(0)
            
    def UpdateFieldsGATHER_ISCSI(self):
        pane = self.Pane()
        pane.ResetFields()
        pane.AddTitleField(Lang('Please enter the configuration details for the iSCSI Storage Repository'))
        pane.AddInputField(Lang('Name', 26), self.srParams.get('name', Lang('iSCSI virtual disk storage')), 'name')
        pane.AddInputField(Lang('Description', 26), '', 'description')
        pane.AddInputField(Lang('Initiator IQN', 26), HotAccessor().local_host.other_config.iscsi_iqn(''), 'localiqn')
        pane.AddInputField(Lang('Port Number', 26), '3260', 'port')
        pane.AddInputField(Lang('Hostname of iSCSI Target', 26), '', 'remotehost')
        pane.AddInputField(Lang('Username', 26), '', 'username')
        pane.AddPasswordField(Lang('Password', 26), '', 'password')

        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
        if pane.CurrentInput() is None:
            pane.InputIndexSet(0)
    
    def UpdateFieldsGATHER_NETAPP(self):
        pane = self.Pane()
        pane.ResetFields()
        pane.AddTitleField(Lang('Please enter the configuration details for the NetApp Storage Repository.  Leave CHAP Username/Password blank if not required.'))
        pane.AddInputField(Lang('Name', 26), self.srParams.get('name', Lang('NetApp virtual disk storage')), 'name')
        pane.AddInputField(Lang('Description', 26), '', 'description')
        pane.AddInputField(Lang('NetApp Filer Address', 26), '', 'target')
        pane.AddInputField(Lang('Username', 26), '', 'username')
        pane.AddPasswordField(Lang('Password', 26), '', 'password')
        pane.AddInputField(Lang('CHAP Username', 26), '', 'chapuser')
        pane.AddPasswordField(Lang('CHAP Password', 26), '', 'chappassword')

        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
        if pane.CurrentInput() is None:
            pane.InputIndexSet(0)
    
    def UpdateFieldsGATHER_HBA(self):
        pane = self.Pane()
        pane.ResetFields()
        pane.AddTitleField(Lang('Hardware HBA (Fibre Channel)'))
        # Text copied from XenCenter
        pane.AddWrappedTextField(Lang('XenServer Hosts support Fibre Channel (FC) storage area networks (SANs) '
            'through Emulex or QLogic host bus adapters (HBAs).  All FC configuration required to expose a FC LUN '
            'to the host must be completed manually, including storage devices, network devices, '
            'and the HBA within the XenServer host.  Once all FC configuration is completed the HBA will expose '
            'a SCSI device backed by the FC LUN to the host.  The SCSI device can then be used to access the '
            'FC LUN as if it were a locally attached SCSI device.'))
        pane.NewLine()
        pane.AddWrappedTextField(Lang('Press <Enter> to scan for HBA devices.'))
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
    
    def UpdateFieldsGATHER_EQUAL(self):
        pane = self.Pane()
        pane.ResetFields()
        pane.AddTitleField(Lang('Please enter the configuration details for the Dell EqualLogic Storage Repository.  Leave CHAP Username/Password blank if not required.'))
        pane.AddInputField(Lang('Name', 26), self.srParams.get('name', Lang('Dell EqualLogic virtual disk storage')), 'name')
        pane.AddInputField(Lang('Description', 26), '', 'description')
        pane.AddInputField(Lang('Filer Address', 26), '', 'target')
        pane.AddInputField(Lang('Username', 26), '', 'username')
        pane.AddPasswordField(Lang('Password', 26), '', 'password')
        pane.AddInputField(Lang('CHAP Username', 26), '', 'chapuser')
        pane.AddPasswordField(Lang('CHAP Password', 26), '', 'chappassword')

        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
        if pane.CurrentInput() is None:
            pane.InputIndexSet(0)
    
    def UpdateFieldsPROBE_NFS(self):
        pane = self.Pane()
        pane.ResetFields()
        pane.AddWarningField('WARNING')
        pane.AddWrappedBoldTextField(Lang('You must ensure that the chosen SR is not in use by any server '
            'that is not a member of this Pool.  Failure to do so may result in data loss.'))
        pane.NewLine()
        pane.AddWrappedBoldTextField(Lang('Please select the Storage Repository to ')+Lang(self.variant.lower()))
        pane.NewLine()

        pane.AddMenuField(self.srMenu, 7) # Only room for 7 menu items
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
    
    def UpdateFieldsPROBE_ISCSI_IQN(self):
        pane = self.Pane()
        pane.ResetFields()
        pane.AddTitleField(Lang('Please select from the list of discovered IQNs.'))

        pane.AddMenuField(self.iqnMenu)
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
    
    def UpdateFieldsPROBE_ISCSI_LUN(self):
        pane = self.Pane()
        pane.ResetFields()
        pane.AddTitleField(Lang('Please select from the list of discovered LUNs.'))

        pane.AddMenuField(self.lunMenu)
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
    
    def UpdateFieldsPROBE_ISCSI_SR(self):
        pane = self.Pane()
        pane.ResetFields()
        pane.AddWarningField('WARNING')
        pane.AddWrappedBoldTextField(Lang('You must ensure that the chosen SR is not in use by any server '
            'that is not a member of this Pool.  Failure to do so may result in data loss.'))
        pane.NewLine()
        pane.AddTitleField(Lang('Please select from the list of discovered Storage Repositories.'))

        pane.AddMenuField(self.srMenu, 7) # Only room for 7 menu items
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
        
    def UpdateFieldsPROBE_NETAPP_AGGREGATE(self):
        pane = self.Pane()
        pane.ResetFields()
        pane.AddTitleField(Lang('Please select from the list of discovered Aggregates.'))

        pane.AddMenuField(self.aggregateMenu)
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
    
    def UpdateFieldsPROBE_NETAPP_FLEXVOLS(self):
        pane = self.Pane()
        pane.ResetFields()
        pane.AddTitleField(Lang('Please enter the number of FlexVols to assign to this Storage Repository.'))

        pane.AddInputField(Lang('Number of FlexVols',24), '8', 'numflexvols')
        
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
        if pane.CurrentInput() is None:
            pane.InputIndexSet(0)
            
    def UpdateFieldsPROBE_NETAPP_PROVISIONING(self):
        pane = self.Pane()
        pane.ResetFields()
        pane.AddTitleField(Lang('Please select the provisioning type for this Storare Repository.'))

        pane.AddMenuField(self.provisioningMenu)
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
    
    def UpdateFieldsPROBE_NETAPP_SR(self):
        pane = self.Pane()
        pane.ResetFields()
        pane.AddWarningField('WARNING')
        pane.AddWrappedBoldTextField(Lang('You must ensure that the chosen SR is not in use by any server '
            'that is not a member of this Pool.  Failure to do so may result in data loss.'))
        pane.NewLine()
        pane.AddTitleField(Lang('Please select from the list of discovered Storage Repositories.'))

        pane.AddMenuField(self.srMenu, 7) # Only room for 7 menu items
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
    
    def UpdateFieldsPROBE_HBA_DEVICE(self):
        pane = self.Pane()
        pane.ResetFields()
        pane.AddTitleField(Lang('Please select from the list of discovered HBA devices.'))

        pane.AddMenuField(self.deviceMenu)
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
    
    def UpdateFieldsPROBE_HBA_NAME(self):
        pane = self.Pane()
        pane.ResetFields()
        if self.hbaWarn:
            pane.AddWarningField(Lang('This device already contains a Storage Repository, and this Create operation will overwrite it.  Choose Attach Existing Storage Repository to retain the original contents.'))
        pane.AddTitleField(Lang('Please enter the name and description for the HBA Storage Repository.'))
        pane.AddInputField(Lang('Name', 26), self.srParams.get('name', Lang('Hardware HBA virtual disk storage')), 'name')
        pane.AddInputField(Lang('Description', 26), '', 'description')

        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
        if pane.CurrentInput() is None:
            pane.InputIndexSet(0)
    
    def UpdateFieldsPROBE_HBA_SR(self):
        pane = self.Pane()
        pane.ResetFields()
        pane.AddWarningField('WARNING')
        pane.AddWrappedBoldTextField(Lang('You must ensure that the chosen SR is not in use by any server '
            'that is not a member of this Pool.  Failure to do so may result in data loss.'))
        pane.NewLine()
        pane.AddTitleField(Lang('Please select from the list of discovered Storage Repositories.'))

        pane.AddMenuField(self.srMenu, 7) # Only room for 7 menu items
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
    
    def UpdateFieldsPROBE_EQUAL_STORAGEPOOL(self):
        pane = self.Pane()
        pane.ResetFields()
        pane.AddTitleField(Lang('Please select from the list of discovered Storage Pools.'))

        pane.AddMenuField(self.storagePoolMenu)
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
    
    def UpdateFieldsPROBE_EQUAL_SR(self):
        pane = self.Pane()
        pane.ResetFields()
        pane.AddWarningField('WARNING')
        pane.AddWrappedBoldTextField(Lang('You must ensure that the chosen SR is not in use by any server '
            'that is not a member of this Pool.  Failure to do so may result in data loss.'))
        pane.NewLine()
        pane.AddTitleField(Lang('Please select from the list of discovered Storage Repositories.'))

        pane.AddMenuField(self.srMenu, 7) # Only room for 7 menu items
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
    
    def UpdateFieldsCONFIRM(self):
        pane = self.Pane()
        pane.ResetFields()
        pane.AddTitleField(Lang('Press <F8> to ')+Lang(self.variant.lower())+Lang(' this Storage Repository'))
        
        pane.AddStatusField(Lang('SR Type', 26), self.srTypeNames[self.createType])
        for name, value in self.extraInfo:
            pane.AddStatusField(name.ljust(26, ' '), value)
        
        pane.NewLine()

        pane.AddKeyHelpField( { Lang("<F8>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
    
    def UpdateFields(self):
        self.Pane().ResetPosition()
        getattr(self, 'UpdateFields'+self.state)() # Despatch method named 'UpdateFields'+self.state

    def ChangeState(self, inState):
        self.state = inState
        self.BuildPane()
        self.UpdateFields()
    
    def HandleKeyINITIAL(self, inKey):
        return self.createMenu.HandleKey(inKey)

    def HandleInputFieldKeys(self, inKey):
        handled = True
        pane = self.Pane()
        if pane.CurrentInput() is None:
            pane.InputIndexSet(0)
        if inKey in ['KEY_ENTER', 'KEY_TAB']:
            pane.ActivateNextInput()
        elif inKey == 'KEY_BTAB':
            pane.ActivatePreviousInput()
        elif pane.CurrentInput().HandleKey(inKey):
            pass # Leave handled as True
        else:
            handled = False
        return handled

    def HandleKeyGATHER_NFS(self, inKey):
        handled = True
        pane = self.Pane()
        if inKey == 'KEY_ENTER' and pane.IsLastInput():
            try:
                inputValues = pane.GetFieldValues()
                if self.variant == 'ATTACH':
                    Layout.Inst().TransientBanner(Lang('Probing for Storage Repositories...'))
                self.HandleNFSData(inputValues)
            except Exception, e:
                pane.InputIndexSet(None)
                Layout.Inst().PushDialogue(InfoDialogue(Lang("Operation Failed"), Lang(e)))
        else:
            handled = self.HandleInputFieldKeys(inKey)
        return handled

    def HandleKeyGATHER_NFS_ISO(self, inKey):
        return self.HandleKeyGATHER_NFS(inKey)

    def HandleKeyGATHER_CIFS_ISO(self, inKey):
        handled = True
        pane = self.Pane()
        if inKey == 'KEY_ENTER' and pane.IsLastInput():
            try:
                inputValues = pane.GetFieldValues()
                self.HandleCIFSData(inputValues)
            except Exception, e:
                pane.InputIndexSet(None)
                Layout.Inst().PushDialogue(InfoDialogue(Lang("Operation Failed"), Lang(e)))
        else:
            handled = self.HandleInputFieldKeys(inKey)
        return handled

    def HandleKeyGATHER_ISCSI(self, inKey):
        handled = True
        pane = self.Pane()
        if inKey == 'KEY_ENTER' and pane.IsLastInput():
            try:
                inputValues = pane.GetFieldValues()
                self.HandleISCSIData(inputValues)
            except Exception, e:
                pane.InputIndexSet(None)
                Layout.Inst().PushDialogue(InfoDialogue(Lang("Operation Failed"), Lang(e)))
        else:
            handled = self.HandleInputFieldKeys(inKey)
        return handled

    def HandleKeyGATHER_NETAPP(self, inKey):
        handled = True
        pane = self.Pane()
        if inKey == 'KEY_ENTER' and pane.IsLastInput():
            try:
                inputValues = pane.GetFieldValues()
                Layout.Inst().TransientBanner(Lang('Probing NetApp...'))
                self.HandleNetAppData(inputValues)
            except Exception, e:
                pane.InputIndexSet(None)
                Layout.Inst().PushDialogue(InfoDialogue(Lang("Operation Failed"), Lang(e)))
        else:
            handled = self.HandleInputFieldKeys(inKey)
        return handled

    def HandleKeyGATHER_HBA(self, inKey):
        handled = True
        pane = self.Pane()
        if inKey == 'KEY_ENTER':
            try:
                # No input fields for HBA
                Layout.Inst().TransientBanner(Lang('Probing for HBA Devices...'))
                self.HandleHBAData({})
            except Exception, e:
                Layout.Inst().PushDialogue(InfoDialogue(Lang("Operation Failed"), Lang(e)))
        else:
            handled = False
        return handled
    
    def HandleKeyPROBE_HBA_NAME(self, inKey):
        handled = True
        pane = self.Pane()
        if inKey == 'KEY_ENTER' and pane.IsLastInput():
            try:
                inputValues = pane.GetFieldValues()
                self.srParams['name'] = inputValues['name']
                self.srParams['description'] = inputValues['description']
                self.extraInfo += [ # Array of tuples
                    (Lang('Name'), self.srParams['name']),
                    (Lang('Description'), self.srParams['description'])
                ]
                if self.variant == 'ATTACH':                    
                    self.ChangeState('PROBE_HBA_SR')
                else:
                    self.ChangeState('CONFIRM')
            except Exception, e:
                pane.InputIndexSet(None)
                Layout.Inst().PushDialogue(InfoDialogue(Lang("Operation Failed"), Lang(e)))
        else:
            handled = self.HandleInputFieldKeys(inKey)
        return handled
    
    def HandleKeyGATHER_EQUAL(self, inKey):
        handled = True
        pane = self.Pane()
        if inKey == 'KEY_ENTER' and pane.IsLastInput():
            try:
                inputValues = pane.GetFieldValues()
                Layout.Inst().TransientBanner(Lang('Probing Dell EqualLogic Server...'))
                self.HandleEqualData(inputValues)
            except Exception, e:
                pane.InputIndexSet(None)
                Layout.Inst().PushDialogue(InfoDialogue(Lang("Operation Failed"), Lang(e)))
        else:
            handled = self.HandleInputFieldKeys(inKey)
        return handled

    def HandleKeyPROBE_NFS(self, inKey):
        return self.srMenu.HandleKey(inKey)

    def HandleKeyPROBE_ISCSI_IQN(self, inKey):
        return self.iqnMenu.HandleKey(inKey)

    def HandleKeyPROBE_ISCSI_LUN(self, inKey):
        return self.lunMenu.HandleKey(inKey)

    def HandleKeyPROBE_ISCSI_SR(self, inKey):
        return self.srMenu.HandleKey(inKey)

    def HandleKeyPROBE_NETAPP_AGGREGATE(self, inKey):
        return self.aggregateMenu.HandleKey(inKey)

    def HandleKeyPROBE_NETAPP_FLEXVOLS(self, inKey):
        handled = True
        pane = self.Pane()
        if inKey == 'KEY_ENTER' and pane.IsLastInput():
            try:
                numFlexVols = int(pane.GetFieldValues()['numflexvols'])
                if numFlexVols < 1 or numFlexVols > 32:
                    raise Exception(Lang('The number of FlexVols must be between 1 and 32'))
                self.srParams['numflexvols'] = numFlexVols
                self.ChangeState('PROBE_NETAPP_PROVISIONING')
            except Exception, e:
                pane.InputIndexSet(None)
                Layout.Inst().PushDialogue(InfoDialogue(Lang("Invalid Value"), Lang(e)))
        else:
            handled = self.HandleInputFieldKeys(inKey)
        return handled

    def HandleKeyPROBE_NETAPP_PROVISIONING(self, inKey):
        return self.provisioningMenu.HandleKey(inKey)
        
    def HandleKeyPROBE_NETAPP_SR(self, inKey):
        return self.srMenu.HandleKey(inKey)

    def HandleKeyPROBE_HBA_DEVICE(self, inKey):
        return self.deviceMenu.HandleKey(inKey)

    def HandleKeyPROBE_HBA_SR(self, inKey):
        return self.srMenu.HandleKey(inKey)
        
    def HandleKeyPROBE_EQUAL_STORAGEPOOL(self, inKey):
        return self.storagePoolMenu.HandleKey(inKey)

    def HandleKeyPROBE_EQUAL_SR(self, inKey):
        return self.srMenu.HandleKey(inKey)

    def HandleKeyCONFIRM(self, inKey):
        handled = False
        if inKey == 'KEY_F(8)':
            try:
                # Despatch method named 'Commit'+self.srCreateType+'_'+self.variant
                getattr(self, 'Commit'+self.createType+'_'+self.variant)() 
            except Exception, e:
                Layout.Inst().PopDialogue()
                Layout.Inst().PushDialogue(InfoDialogue(Lang("Operation Failed"), Lang(e)))
            handled = True
        return handled

    def HandleKey(self,  inKey):
        handled = False
        if hasattr(self, 'HandleKey'+self.state):
            handled = getattr(self, 'HandleKey'+self.state)(inKey)
        
        if not handled and inKey in ('KEY_ESCAPE', 'KEY_LEFT'):
            Layout.Inst().PopDialogue()
            handled = True

        return handled

    def HandleNFSData(self, inParams):
        self.srParams = inParams

        match = re.match(r'([^:]*):([^:]*)$', self.srParams['sharename'])
        if not match:
            raise Exception(Lang('Share name must contain a single colon, e.g. server:/path'))
        self.srParams['server'] = IPUtils.AssertValidNetworkName(match.group(1))
        self.srParams['serverpath'] = IPUtils.AssertValidNFSPathName(match.group(2))
        self.extraInfo = [ # Array of tuples
            (Lang('Name'), self.srParams['name']),
            (Lang('Share Name'), self.srParams['sharename'])
            ]

        if self.variant == 'CREATE' or self.createType == 'NFS_ISO':
            self.ChangeState('CONFIRM')
        elif self.variant == 'ATTACH':
            xmlSRList = Task.Sync(lambda x: x.xenapi.SR.probe(
                HotAccessor().local_host_ref().OpaqueRef(), # host
                { # device_config
                    'server':self.srParams['server'],
                    'serverpath':self.srParams['serverpath'],
                },
                'nfs' # type
                )
            )
            if xmlSRList == '':
                self.srChoices = []
            else:
                # Parse XML for UUID values
                xmlDoc = xml.dom.minidom.parseString(xmlSRList)
                self.srChoices = [ str(node.firstChild.nodeValue.strip()) for node in xmlDoc.getElementsByTagName("UUID") ]
                
            self.ChangeState('PROBE_NFS')
        else:
            raise Exception('Bad self.variant') # Logic error
    
    def HandleCIFSData(self, inParams):
        self.srParams = inParams

        match = re.match(r'\\\\([^\\]*)\\([^\\]*)$', self.srParams['sharename'])
        if not match:
            raise Exception(Lang('Share name must be of the form \\\\server\\path'))
        self.srParams['server'] = IPUtils.AssertValidNetworkName(match.group(1))
        self.srParams['serverpath'] = IPUtils.AssertValidCIFSPathName(match.group(2))
        self.extraInfo = [ # Array of tuples
            (Lang('Name'), self.srParams['name']),
            (Lang('Share Name'), self.srParams['sharename'])
            ]

        self.ChangeState('CONFIRM')
        
    def HandleISCSIData(self, inParams):
        self.srParams = inParams
        self.extraInfo = [ # Array of tuples
            (Lang('Initiator IQN'), self.srParams['localiqn']),
            (Lang('Port Number'), self.srParams['port']),
            (Lang('Hostname of iSCSI Target'), self.srParams['remotehost']),
            (Lang('Username'), self.srParams['username']),
            (Lang('Password'), '*' * len(self.srParams['password']))
        ]
        try:
            # This task will raise an exception with details of available IQNs
            Task.Sync(lambda x: x.xenapi.SR.probe(
                HotAccessor().local_host_ref().OpaqueRef(), # host
                { # device_config
                    'target':self.srParams['remotehost'],
                    'port':self.srParams['port']
                },
                'lvmoiscsi' # type
                )
            )
        except XenAPI.Failure, e:
            if e.details[0] != 'SR_BACKEND_FAILURE_96':
                raise
            # Parse XML for UUID values
            self.iqnChoices = []
            if e.details[3] != '':
                xmlDoc = xml.dom.minidom.parseString(e.details[3])
                for tgt in xmlDoc.getElementsByTagName('TGT'):
                    try:
                        index = str(tgt.getElementsByTagName('Index')[0].firstChild.nodeValue.strip())
                        iqn =  str(tgt.getElementsByTagName('TargetIQN')[0].firstChild.nodeValue.strip())
                        self.iqnChoices.append(Struct(
                            portal = self.srParams['remotehost']+':'+self.srParams['port'],
                            tgpt=index,
                            name=iqn,
                            iqn=iqn))
                            
                    except Exception, e:
                        pass # Ignore failures
                
        self.ChangeState('PROBE_ISCSI_IQN')

    def NetAppBaseConfig(self):
        retVal = {
            'target':self.srParams['target'],
            'username':self.srParams['username'],
            'password':self.srParams['password']        
        }
        if self.srParams['chapuser'] != '':
            retVal.update({
                'chapuser':self.srParams['chapuser'],
                'chappassword':self.srParams['chappassword']
            })
        return retVal

    def HandleNetAppData(self, inParams):
        self.srParams = inParams
        self.extraInfo = [ # Array of tuples
            (Lang('NetApp Filer Address'), self.srParams['target']),
            (Lang('Username'), self.srParams['username']),
            (Lang('Password'), '*' * len(self.srParams['password'])),
            (Lang('CHAP Username'), self.srParams['chapuser']),
            (Lang('CHAP Password'), '*' * len(self.srParams['chappassword']))
        ]

        if self.variant == 'CREATE':
            # To create, we need the list of aggregates, which is obtained using a fake SR.create.
            # This will fail because we're not supplying an aggregate name
            try:
                srRef = Task.Sync(lambda x: x.xenapi.SR.create(
                    HotAccessor().local_host_ref().OpaqueRef(), # host
                    self.NetAppBaseConfig(), # device_config
                    '0', # physical_size
                    self.srParams['name'], # name_label
                    self.srParams['description'], # name_description
                    'netapp', # type
                    'user', # content_type
                    True # shared
                    )
                )
            except XenAPI.Failure, e:
                if e.details[0] != 'SR_BACKEND_FAILURE_123':
                    raise
                # Parse XML for UUID values
                self.aggregateChoices = []
                if e.details[3] != '':
                    xmlDoc = xml.dom.minidom.parseString(e.details[3])
                    for aggregate in xmlDoc.getElementsByTagName('Aggr'):
                        try:
                            name = str(aggregate.getElementsByTagName('Name')[0].firstChild.nodeValue.strip())
                            size = str(aggregate.getElementsByTagName('Size')[0].firstChild.nodeValue.strip())
                            disks = str(aggregate.getElementsByTagName('Disks')[0].firstChild.nodeValue.strip())
                            raidType = str(aggregate.getElementsByTagName('RAIDType')[0].firstChild.nodeValue.strip())
                            asisdedup = str(aggregate.getElementsByTagName('asis_dedup')[0].firstChild.nodeValue.strip())
                            self.aggregateChoices.append(Struct(
                                name = name,
                                size = size,
                                disks = disks,
                                raidType = raidType,
                                asisdedup = asisdedup)) # NetApp's Advanced Single Instance Storage Deduplication, 'true' if supported
                                
                        except Exception, e:
                            pass # Ignore failures
            self.ChangeState('PROBE_NETAPP_AGGREGATE')
        elif self.variant=='ATTACH':
            # This probe returns xml directly
            xmlOutput = Task.Sync(lambda x: x.xenapi.SR.probe(
                HotAccessor().local_host_ref().OpaqueRef(), # host
                self.NetAppBaseConfig(), # device_config
                'netapp' # type
                )
            )
    
            self.netAppSRChoices = []
            xmlDoc = xml.dom.minidom.parseString(xmlOutput)
            for xmlSR in xmlDoc.getElementsByTagName('SR'):
                try:
                    uuid = str(xmlSR.getElementsByTagName('UUID')[0].firstChild.nodeValue.strip())
                    size =  str(xmlSR.getElementsByTagName('Size')[0].firstChild.nodeValue.strip())
                    aggregate =  str(xmlSR.getElementsByTagName('Aggregate')[0].firstChild.nodeValue.strip())
                    self.netAppSRChoices.append(Struct(
                        uuid = uuid,
                        size = size,
                        aggregate = aggregate
                    ))
                        
                except Exception, e:
                    pass # Ignore failures
                    
            self.ChangeState('PROBE_NETAPP_SR')
        else:
            raise Exception('bad self.variant') # Logic error

    def HandleHBAData(self, inParams):
        self.extraInfo = []
        # To create, we need the list of devices, which is obtained using SR.probe.
        # This will fail because we're not supplying a device name
        try:
            srRef = Task.Sync(lambda x: x.xenapi.SR.probe(
                HotAccessor().local_host_ref().OpaqueRef(), # host
                {}, # device_config
                'lvmohba', # type
                )
            )
        except XenAPI.Failure, e:
            if e.details[0] != 'SR_BACKEND_FAILURE_90':
                raise
            # Parse XML for UUID values
            self.deviceChoices = []
            if e.details[3] != '':
                xmlDoc = xml.dom.minidom.parseString(e.details[3])
                for device in xmlDoc.getElementsByTagName('BlockDevice'):
                    try:
                        deviceInfo = Struct()
                        for name in ('path', 'SCSIid', 'vendor', 'serial', 'size', 'adapter', 'channel', 'id', 'lun', 'hba'):
                            setattr(deviceInfo, name.lower(), str(device.getElementsByTagName(name)[0].firstChild.nodeValue.strip()))
                        self.deviceChoices.append(deviceInfo) 
                            
                    except Exception, e:
                        pass # Ignore failures
        self.ChangeState('PROBE_HBA_DEVICE')

    def EqualBaseConfig(self):
        retVal = {
            'target':self.srParams['target'],
            'username':self.srParams['username'],
            'password':self.srParams['password']        
        }
        if self.srParams['chapuser'] != '':
            retVal.update({
                'chapuser':self.srParams['chapuser'],
                'chappassword':self.srParams['chappassword']
            })
        return retVal

    def HandleEqualData(self, inParams):
        self.srParams = inParams
        self.extraInfo = [ # Array of tuples
            (Lang('Filer Address'), self.srParams['target']),
            (Lang('Username'), self.srParams['username']),
            (Lang('Password'), '*' * len(self.srParams['password'])),
            (Lang('CHAP Username'), self.srParams['chapuser']),
            (Lang('CHAP Password'), '*' * len(self.srParams['chappassword']))
        ]

        if self.variant == 'CREATE':
            # To create, we need the list of aggregates, which is obtained using a fake SR.create.
            # This will fail because we're not supplying an aggregate name
            try:
                srRef = Task.Sync(lambda x: x.xenapi.SR.create(
                    HotAccessor().local_host_ref().OpaqueRef(), # host
                    self.NetAppBaseConfig(), # device_config
                    '0', # physical_size
                    self.srParams['name'], # name_label
                    self.srParams['description'], # name_description
                    'equal', # type
                    'user', # content_type
                    True # shared
                    )
                )
            except XenAPI.Failure, e:
                if e.details[0] != 'SR_BACKEND_FAILURE_163':
                    raise
                # Parse XML for UUID values
                self.storagePoolChoices = []
                if e.details[3] != '':
                    xmlDoc = xml.dom.minidom.parseString(e.details[3])
                    for storagePool in xmlDoc.getElementsByTagName('StoragePool'):
                        try:
                            storageInfo = Struct()
                            for name in ('Name', 'Default', 'Members', 'Volumes', 'Capacity', 'FreeSpace'):
                                setattr(storageInfo, name.lower(), storagePool.getElementsByTagName(name)[0].firstChild.nodeValue.strip())
                            self.storagePoolChoices.append(storageInfo) 
                                
                        except Exception, e:
                            pass # Ignore failures
            self.ChangeState('PROBE_EQUAL_STORAGEPOOL')
        elif self.variant=='ATTACH':
            # This probe returns xml directly
            xmlOutput = Task.Sync(lambda x: x.xenapi.SR.probe(
                HotAccessor().local_host_ref().OpaqueRef(), # host
                self.EqualBaseConfig(), # device_config
                'equal' # type
                )
            )
    
            self.equalSRChoices = []
            xmlDoc = xml.dom.minidom.parseString(xmlOutput)
            for xmlSR in xmlDoc.getElementsByTagName('SR'):
                try:
                    uuid = str(xmlSR.getElementsByTagName('UUID')[0].firstChild.nodeValue.strip())
                    size =  str(xmlSR.getElementsByTagName('Size')[0].firstChild.nodeValue.strip())
                    self.equalSRChoices.append(Struct(
                        uuid = uuid,
                        size = size
                    ))
                        
                except Exception, e:
                    pass # Ignore failures
                
            self.ChangeState('PROBE_EQUAL_SR')
        else:
            raise Exception('bad self.variant') # Logic error


    def HandleCreateChoice(self, inChoice):
        self.createType = inChoice
        
        self.ChangeState('GATHER_'+inChoice)

    def HandleProbeChoice(self, inChoice):
        self.srParams['uuid'] = inChoice
        self.extraInfo.append( (Lang('SR ID'), inChoice) ) # Append tuple, so double brackets
        self.ChangeState('CONFIRM')

    def HandleIQNChoice(self, inChoice):
        self.srParams['iqn'] = inChoice
        self.extraInfo.append( (Lang('IQN'), inChoice.name) ) # Append tuple, so double brackets
        Layout.Inst().TransientBanner(Lang('Probing for LUNs...'))
        self.lunChoices = []
        try:
            # This task will raise an exception with details of available LUNs
            Task.Sync(lambda x: x.xenapi.SR.probe(
                    HotAccessor().local_host_ref().OpaqueRef(), # host
                    { # device_config
                        'target':self.srParams['remotehost'],
                        'port':self.srParams['port'],
                        'targetIQN':self.srParams['iqn'].iqn
                    },
                    'lvmoiscsi' # type
                    )
                )
        except XenAPI.Failure, e:
            # Parse XML for UUID values
            if e.details[0] != 'SR_BACKEND_FAILURE_107':
                raise
            if e.details[3] != '':
                xmlDoc = xml.dom.minidom.parseString(e.details[3])
                for xmlLUN in xmlDoc.getElementsByTagName('LUN'):
                    try:
                        record = Struct()
                        for name in ('vendor', 'LUNid', 'size', 'SCSIid'):
                            setattr(record, name, str(xmlLUN.getElementsByTagName(name)[0].firstChild.nodeValue.strip()))
                            
                        self.lunChoices.append(record)
                            
                    except Exception, e:
                        pass # Ignore failures
            
        self.ChangeState('PROBE_ISCSI_LUN')

    def HandleLUNChoice(self, inChoice):
        self.srParams['lun'] = inChoice
        self.extraInfo.append( (Lang('LUN'), str(inChoice.LUNid)) ) # Append tuple, so double brackets
        if self.variant == 'CREATE':
            self.ChangeState('CONFIRM')
        else:
            Layout.Inst().TransientBanner(Lang('Probing for Storage Repositories...'))
            self.srChoices = []

            xmlResult = Task.Sync(lambda x: x.xenapi.SR.probe(
                HotAccessor().local_host_ref().OpaqueRef(), # host
                { # device_config
                    'target':self.srParams['remotehost'],
                    'port':self.srParams['port'],
                    'targetIQN':self.srParams['iqn'].iqn,
                    'SCSIid':self.srParams['lun'].SCSIid
                },
                'lvmoiscsi' # type
                )
            )

            xmlDoc = xml.dom.minidom.parseString(xmlResult)
            if xmlDoc == '':
                self.srChoices = []
            else:
                self.srChoices = [ str(node.firstChild.nodeValue.strip()) for node in xmlDoc.getElementsByTagName("UUID") ]
    
            self.ChangeState('PROBE_ISCSI_SR')

    def HandleiSCSISRChoice(self, inChoice):
        self.srParams['uuid'] = inChoice
        self.extraInfo.append( (Lang('SR ID'), inChoice) ) # Append tuple, so double brackets
        self.ChangeState('CONFIRM')

    def HandleAggregateChoice(self, inChoice):
        self.srParams['aggregate'] = inChoice
        self.extraInfo.append( (Lang('Aggregate'), inChoice.name) ) # Append tuple, so double brackets
        self.ChangeState('PROBE_NETAPP_FLEXVOLS')

    def HandleProvisioningChoice(self, inChoice):
        self.srParams['provisioning'] = inChoice
        self.extraInfo.append( (Lang('Provisioning'), self.NetAppProvisioningName(inChoice)) ) # Append tuple, so double brackets
        self.ChangeState('CONFIRM')

    def HandleNetAppSRChoice(self, inChoice):
        self.srParams['uuid'] = inChoice.uuid
        self.extraInfo.append( (Lang('SR ID'), inChoice.uuid) ) # Append tuple, so double brackets
        self.ChangeState('CONFIRM')

    def HandleDeviceChoice(self, inChoice):
        self.srParams['device'] = inChoice.path
        self.extraInfo.append( (Lang('Device'), inChoice.vendor + ' ' + inChoice.serial) ) # Append tuple, so double brackets
        xmlResult = Task.Sync(lambda x: x.xenapi.SR.probe(
            HotAccessor().local_host_ref().OpaqueRef(), # host
            { 'device' : self.srParams['device'] }, # device_config
            'lvmohba' # type
            )
        )
        xmlDoc = xml.dom.minidom.parseString(xmlResult)
        if xmlDoc == '':
            self.srChoices = []
        else:
            self.srChoices = [ str(node.firstChild.nodeValue.strip()) for node in xmlDoc.getElementsByTagName("UUID") ]

        self.hbaWarn = ( self.variant == 'CREATE' and len(self.srChoices) != 0 )
            
        self.ChangeState('PROBE_HBA_NAME')

    def HandleHBASRChoice(self, inChoice):
        self.srParams['uuid'] = inChoice
        self.extraInfo.append( (Lang('SR ID'), inChoice) ) # Append tuple, so double brackets
        self.ChangeState('CONFIRM')

    def HandleStoragePoolChoice(self, inChoice):
        self.srParams['storagepool'] = inChoice.name
        self.extraInfo.append( (Lang('Storage Pool'), inChoice.name) ) # Append tuple, so double brackets
        self.ChangeState('CONFIRM')

    def HandleEqualSRChoice(self, inChoice):
        self.srParams['uuid'] = inChoice.uuid
        self.extraInfo.append( (Lang('SR ID'), inChoice.uuid) ) # Append tuple, so double brackets
        self.ChangeState('CONFIRM')

    def CommitCreate(self, inType, inDeviceConfig, inOtherConfig = None):
        Layout.Inst().PopDialogue()
        Layout.Inst().TransientBanner(Lang('Creating Storage Repository...'))
        try:
            srRef = Task.Sync(lambda x: x.xenapi.SR.create(
                HotAccessor().local_host_ref().OpaqueRef(), # host
                inDeviceConfig,
                '0', # physical_size
                self.srParams['name'], # name_label
                self.srParams['description'], # name_description
                inType, # type
                'user', # content_type
                True # shared
                )
            )
            
            # Set values in other_config only if the SR.create operation hasn't already set them
            for key, value in FirstValue(inOtherConfig, {}).iteritems():
                try:
                    Task.Sync(lambda x:x.xenapi.SR.add_to_other_config(srRef, key, value))
                except:
                    pass #  Ignore failure

            Data.Inst().Update()
            Data.Inst().SetPoolSRIfRequired(srRef)
            Layout.Inst().PushDialogue(InfoDialogue(Lang("Storage Repository Creation Successful")))
            
        except Exception, e:
            Layout.Inst().PushDialogue(InfoDialogue(Lang("Storage Repository Creation Failed"), Lang(e)))

    def CommitAttach(self, inType, inDeviceConfig, inOtherConfig, inContentType):
        srRef = None
        
        for sr in HotAccessor().sr:
            if sr.uuid() == self.srParams['uuid']:
                # SR already exists, so check whether it's fully configured
                if len(sr.PBDs()) == 0:
                    # SR is detached (no PBDs).  Skip the SR.introduce stage but create the PBDs
                    srRef = sr.HotOpaqueRef().OpaqueRef()
                else:
                    # SR is already fully attached
                    raise Exception(Lang('SR ID ')+self.srParams['uuid']+Lang(" is already attached to the system as '")+sr.name_label(Lang('<Unknown>'))+"'")

        Layout.Inst().PopDialogue()
        Layout.Inst().TransientBanner(Lang('Attaching Storage Repository...'))
        pbdList = []
        pluggedPBDList = []
        try:
            if srRef is None:
                srRef = Task.Sync(lambda x: x.xenapi.SR.introduce(
                    self.srParams['uuid'], # uuid
                    self.srParams['name'], # name_label
                    self.srParams['description'], # name_description
                    inType, # type
                    inContentType, # content_type
                    True # shared
                    )
                )
    
                # Set values in other_config only if the SR.introduce operation hasn't already set them
                for key, value in FirstValue(inOtherConfig, {}).iteritems():
                    try:
                        Task.Sync(lambda x:x.xenapi.SR.add_to_other_config(srRef, key, value))
                    except:
                        pass #  Ignore failure

            for host in HotAccessor().host:
                pbdList.append(Task.Sync(lambda x: x.xenapi.PBD.create({
                    'host':host.HotOpaqueRef().OpaqueRef(), # Host ref
                    'SR':srRef, # SR ref
                    'device_config':inDeviceConfig
                })))
            
            for pbd in pbdList:
                Task.Sync(lambda x: x.xenapi.PBD.plug(pbd))
                pluggedPBDList.append(pbd)
            
            Data.Inst().Update()
            if inContentType != 'iso':
                Data.Inst().SetPoolSRIfRequired(srRef)
            Layout.Inst().PushDialogue(InfoDialogue(Lang("Storage Repository Attachment Successful")))

        except Exception, e:
            message = Lang(e)
            # Attempt to undo the work we've done, because the SR is incomplete
            try:
                for pluggedPBD in pluggedPBDList:
                    Task.Sync(lambda x: x.xenapi.PBD.unplug(pluggedPBD))
                for pbd in pbdList:
                    Task.Sync(lambda x: x.xenapi.PBD.destroy(pbd))
                    
                Task.Sync(lambda x: x.xenapi.SR.forget(srRef))
                
            except Exception, e:
                message += Lang('.  Attempts to rollback also failed: ')+Lang(e)

            Layout.Inst().PushDialogue(InfoDialogue(Lang("Storage Repository Attachment Failed"), message))

    def CommitNFS_CREATE(self):
        self.CommitCreate('nfs', { # device_config
            'server':self.srParams['server'],
            'serverpath':self.srParams['serverpath'],
        },
        { # Set auto-scan to false for non-ISO SRs
            'auto-scan':'false'
        })
        
    def CommitNFS_ATTACH(self):
        self.CommitAttach('nfs', { # device_config
            'server':self.srParams['server'],
            'serverpath':self.srParams['serverpath'],
        },
        {}, # other_config
        'user')

    def CommitNFS_ISO_ATTACH(self):
        self.srParams['uuid'] = commands.getoutput('/usr/bin/uuidgen')
        self.CommitAttach('iso', { # device_config
            'location':self.srParams['server']+':'+self.srParams['serverpath'],
            'options':self.srParams['options']
        },
        { # Set auto-scan to true for ISO SRs
            'auto-scan':'true'
        },
        'iso'
        )

    def CommitCIFS_ISO_ATTACH(self):
        self.srParams['uuid'] = commands.getoutput('/usr/bin/uuidgen')
        deviceConfig = {
            'location':'//'+self.srParams['server']+'/'+self.srParams['serverpath'],
            'type':'cifs',
            'options':self.srParams['options']
        }
        if self.srParams['username'] != '':
            deviceConfig.update({
                'username' : self.srParams['username'],
                'cifspassword' : self.srParams['cifspassword']
            })
        self.CommitAttach('iso', 
            deviceConfig,
            { # Set auto-scan to true for ISO SRs
                'auto-scan':'true'
            },
            'iso'
        )

    def CommitISCSI_CREATE(self):
        self.CommitCreate('lvmoiscsi', { # device_config
            'target':self.srParams['remotehost'],
            'port':self.srParams['port'],
            'targetIQN':self.srParams['iqn'].iqn,
            'SCSIid':self.srParams['lun'].SCSIid
            },
            { # Set auto-scan to false for non-ISO SRs
                'auto-scan':'false'
            }
        )
        
    def CommitISCSI_ATTACH(self):
        self.CommitAttach('lvmoiscsi', { # device_config
            'target':self.srParams['remotehost'],
            'port':self.srParams['port'],
            'targetIQN':self.srParams['iqn'].iqn,
            'SCSIid':self.srParams['lun'].SCSIid
            },
            {}, # other_config
            'user' # content_type
        )

    def CommitNETAPP_CREATE(self):
        deviceConfig = self.NetAppBaseConfig()
        deviceConfig.update({
            'aggregate':self.srParams['aggregate'].name,
            'FlexVols':str(self.srParams['numflexvols'])
        })
        deviceConfig.update(self.NetAppProvisioningConfig(self.srParams['provisioning']))
        self.CommitCreate('netapp',
            deviceConfig,
            { # Set auto-scan to false for non-ISO SRs
                'auto-scan':'false'
            }
        )

    def CommitNETAPP_ATTACH(self):
        deviceConfig = self.NetAppBaseConfig()
        
        self.CommitAttach('netapp',
            deviceConfig, # device_config
            {}, # other_config
            'user' # content_type
        )
        
    def CommitHBA_CREATE(self):
        deviceConfig = { 'device' : self.srParams['device'] }
        self.CommitCreate('lvmohba',
            deviceConfig,
            { # Set auto-scan to false for non-ISO SRs
                'auto-scan':'false'
            }
        )
    
    def CommitHBA_ATTACH(self):
        deviceConfig = { 'device' : self.srParams['device'] }
        
        self.CommitAttach('lvmohba',
            deviceConfig, # device_config
            {}, # other_config
            'user' # content_type
        )
    
    def CommitEQUAL_CREATE(self):
        deviceConfig = self.EqualBaseConfig()
        deviceConfig.update({
            'storagepool':self.srParams['storagepool']
        })
        self.CommitCreate('equal',
            deviceConfig,
            { # Set auto-scan to false for non-ISO SRs
                'auto-scan':'false'
            }
        )

    def CommitEQUAL_ATTACH(self):
        deviceConfig = self.EqualBaseConfig()
        
        self.CommitAttach('equal',
            deviceConfig, # device_config
            {}, # other_config
            'user' # content_type
        )


class XSFeatureSRCreate:
    @classmethod
    def CreateStatusUpdateHandler(cls, inPane):
        inPane.AddTitleField(Lang("Create New Storage Repository"))
    
        inPane.AddWrappedTextField(Lang(
            "This option is used to create a new Storage Repository."))
    
    @classmethod
    def AttachStatusUpdateHandler(cls, inPane):
        inPane.AddTitleField(Lang("Attach Existing Storage Repository"))
    
        inPane.AddWrappedTextField(Lang(
            "This option is used to attach a Storage Repository or ISO library that already exists."))
    
    @classmethod
    def CreateActivateHandler(cls):
        DialogueUtils.AuthenticatedOnly(lambda: Layout.Inst().PushDialogue(SRNewDialogue('CREATE')))
    
    @classmethod
    def AttachActivateHandler(cls):
        DialogueUtils.AuthenticatedOnly(lambda: Layout.Inst().PushDialogue(SRNewDialogue('ATTACH')))
    
    def Register(self):
        Importer.RegisterNamedPlugIn(
            self,
            'SR_CREATE', # Key of this plugin for replacement, etc.
            {
                'menuname' : 'MENU_DISK',
                'menupriority' : 200,
                'menutext' : Lang('Create New Storage Repository') ,
                'statusupdatehandler' : self.CreateStatusUpdateHandler,
                'activatehandler' : self.CreateActivateHandler
            }
        )

        Importer.RegisterNamedPlugIn(
            self,
            'SR_ATTACH', # Key of this plugin for replacement, etc.
            {
                'menuname' : 'MENU_DISK',
                'menupriority' : 300,
                'menutext' : Lang('Attach Existing Storage Repository') ,
                'statusupdatehandler' : self.AttachStatusUpdateHandler,
                'activatehandler' : self.AttachActivateHandler
            }
        )

# Register this plugin when module is imported
XSFeatureSRCreate().Register()
