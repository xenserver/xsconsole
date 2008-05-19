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
        'CIFS_ISO': Lang('Windows File Sharing (CIFS) ISO Library'),
        'NFS_ISO': Lang('NFS ISO Library')
    }    
    
    def __init__(self, inVariant):

        Dialogue.__init__(self)
        self.variant = inVariant
        self.srParams = {}
        self.createMenu = Menu()

        if self.variant == 'CREATE':
            choices = ['NFS', 'ISCSI']
        else:
            choices = ['NFS_ISO', 'ISCSI', 'NFS']
        
        #choices = ['NFS', 'ISCSI', 'NETAPP', 'CIFS_ISO', 'NFS_ISO']
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
        
    def BuildPanePROBE_NFS(self):
        self.srMenu = Menu()
        for srChoice in self.srChoices:
            self.srMenu.AddChoice(name = srChoice,
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
            self.srMenu.AddChoice(name = srChoice,
                onAction = self.HandleiSCSISRChoice,
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
        pane.AddInputField(Lang('Name', 16), self.srParams.get('name', Lang('NFS Virtual Disk Storage')), 'name')
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
    
    def UpdateFieldsGATHER_ISCSI(self):
        pane = self.Pane()
        pane.ResetFields()
        pane.AddTitleField(Lang('Please enter the configuration details for the iSCSI Storage Repository'))
        pane.AddInputField(Lang('Name', 26), self.srParams.get('name', Lang('iSCSI Virtual Disk Storage')), 'name')
        pane.AddInputField(Lang('Description', 26), '', 'description')
        pane.AddInputField(Lang('Initiator IQN', 26), HotAccessor().local_host.other_config.iscsi_iqn(''), 'localiqn')
        pane.AddInputField(Lang('Port Number', 26), '3260', 'port')
        pane.AddInputField(Lang('Hostname of iSCSI Target', 26), '', 'remotehost')
        pane.AddInputField(Lang('Username', 26), '', 'username')
        pane.AddPasswordField(Lang('Password', 26), '', 'password')

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

        pane.AddMenuField(self.srMenu)
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
        pane.AddTitleField(Lang('Please select from the list of discovered Storage Repositories.'))

        pane.AddMenuField(self.srMenu)
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

    def HandleKeyGATHER_NFS(self, inKey):
        handled = True
        pane = self.Pane()
        if pane.CurrentInput() is None:
            pane.InputIndexSet(0)
        if inKey == 'KEY_ENTER':
            if pane.IsLastInput():
                try:
                    inputValues = pane.GetFieldValues()
                    if self.variant == 'ATTACH':
                        Layout.Inst().TransientBanner(Lang('Probing for Storage Repositories...'))
                    self.HandleNFSData(inputValues)
                except Exception, e:
                    pane.InputIndexSet(None)
                    Layout.Inst().PushDialogue(InfoDialogue(Lang("Operation Failed"), Lang(e)))
            else:
                pane.ActivateNextInput()
        elif inKey == 'KEY_TAB':
            pane.ActivateNextInput()
        elif inKey == 'KEY_BTAB':
            pane.ActivatePreviousInput()
        elif pane.CurrentInput().HandleKey(inKey):
            pass # Leave handled as True
        else:
            handled = False
        return handled

    def HandleKeyGATHER_NFS_ISO(self, inKey):
        return self.HandleKeyGATHER_NFS(inKey)

    def HandleKeyGATHER_ISCSI(self, inKey):
        handled = True
        pane = self.Pane()
        if pane.CurrentInput() is None:
            pane.InputIndexSet(0)
        if inKey == 'KEY_ENTER':
            if pane.IsLastInput():
                try:
                    inputValues = pane.GetFieldValues()
                    self.HandleISCSIData(inputValues)
                except Exception, e:
                    pane.InputIndexSet(None)
                    Layout.Inst().PushDialogue(InfoDialogue(Lang("Operation Failed"), Lang(e)))
            else:
                pane.ActivateNextInput()
        elif inKey == 'KEY_TAB':
            pane.ActivateNextInput()
        elif inKey == 'KEY_BTAB':
            pane.ActivatePreviousInput()
        elif pane.CurrentInput().HandleKey(inKey):
            pass # Leave handled as True
        else:
            handled = False
        return handled

    def HandleKeyPROBE_NFS(self, inKey):
        return self.srMenu.HandleKey(inKey)

    def HandleKeyPROBE_ISCSI_IQN(self, inKey):
        return self.iqnMenu.HandleKey(inKey)

    def HandleKeyPROBE_ISCSI_LUN(self, inKey):
        return self.lunMenu.HandleKey(inKey)

    def HandleKeyPROBE_ISCSI_SR(self, inKey):
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
            self.srChoices = [ str(node.firstChild.nodeValue.strip()) for node in xmlDoc.getElementsByTagName("UUID") ]
    
            self.ChangeState('PROBE_ISCSI_SR')

    def HandleiSCSISRChoice(self, inChoice):
        self.srParams['uuid'] = inChoice
        self.extraInfo.append( (Lang('SR ID'), inChoice) ) # Append tuple, so double brackets
        self.ChangeState('CONFIRM')

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
            # Parse XML for UUID values
            xmlDoc = xml.dom.minidom.parseString(xmlSRList)
            self.srChoices = [ str(node.firstChild.nodeValue.strip()) for node in xmlDoc.getElementsByTagName("UUID") ]
                
            self.ChangeState('PROBE_NFS')
        else:
            raise Exception('Bad self.variant') # Logic error
    
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
            # Parse XML for UUID values
            self.iqnChoices = []
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
    
    def CommitCreate(self, inType, inDeviceConfig, inOtherConfig = None):
        Layout.Inst().PopDialogue()
        Layout.Inst().TransientBanner(Lang('Creating SR...'))
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

            Layout.Inst().PushDialogue(InfoDialogue(Lang("Storage Repository Creation Successful")))
        except Exception, e:
            Layout.Inst().PushDialogue(InfoDialogue(Lang("Storage Repository Creation Failed"), Lang(e)))

    def CommitAttach(self, inType, inDeviceConfig, inOtherConfig, inContentType):
        for sr in HotAccessor().sr:
            if sr.uuid() == self.srParams['uuid']:
                raise Exception(Lang('SR ID ')+self.srParams['uuid']+Lang(" is already attached to the system as '")+sr.name_label(Lang('<Unknown>'))+"'")

        Layout.Inst().PopDialogue()
        Layout.Inst().TransientBanner(Lang('Attaching Storage Repository...'))
        srRef = None
        pbdList = []
        pluggedPBDList = []
        try:
            srRef = Task.Sync(lambda x: x.xenapi.SR.introduce(
                self.srParams['uuid'], # uuid
                self.srParams['name'], # name_label
                self.srParams['description'], # name_description
                inType, # type
                inContentType, # content_type
                True # shared
                )
            )

            for host in HotAccessor().host:
                pbdList.append(Task.Sync(lambda x: x.xenapi.PBD.create({
                    'host':host.HotOpaqueRef().OpaqueRef(), # Host ref
                    'SR':srRef, # SR ref
                    'device_config':inDeviceConfig
                })))
            
            for pbd in pbdList:
                Task.Sync(lambda x: x.xenapi.PBD.plug(pbd))
                pluggedPBDList.append(pbd)
                
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

    def CommitISCSI_CREATE(self):
        self.CommitCreate('lvmoiscsi', { # device_config
            'target':self.srParams['remotehost'],
            'port':self.srParams['port'],
            'targetIQN':self.srParams['iqn'].iqn,
            'SCSIid':self.srParams['lun'].SCSIid
        },
        { # Set auto-scan to false for non-ISO SRs
            'auto-scan':'false'
        })
        
    def CommitISCSI_ATTACH(self):
        self.CommitAttach('lvmoiscsi', { # device_config
            'target':self.srParams['remotehost'],
            'port':self.srParams['port'],
            'targetIQN':self.srParams['iqn'].iqn,
            'SCSIid':self.srParams['lun'].SCSIid
        },
        {}, # other_config
        'user')
        
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
                'menupriority' : 50,
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
                'menupriority' : 40,
                'menutext' : Lang('Attach Existing Storage Repository') ,
                'statusupdatehandler' : self.AttachStatusUpdateHandler,
                'activatehandler' : self.AttachActivateHandler
            }
        )

# Register this plugin when module is imported
XSFeatureSRCreate().Register()
