# Copyright (c) Citrix Systems 2007. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

if __name__ == "__main__":
    raise Exception("This script is a plugin for xsconsole and cannot run independently")
    
from XSConsoleStandard import *
from XSConsolePlugIn import *

class InterfaceDialogue(Dialogue):
    def __init__(self):
        Dialogue.__init__(self)
        
        choiceDefs = []

        self.nic=None
        self.converting = False
        currentPIF = None
        choiceArray = []
        for i in range(len(Data.Inst().host.PIFs([]))):
            pif = Data.Inst().host.PIFs([])[i]
            if currentPIF is None and pif['management']:
                self.nic = i # Record this as best guess of current NIC
                currentPIF = pif
            choiceName = pif['device']+": "+pif['metrics']['device_name']+" "
            if pif['metrics']['carrier']:
                choiceName += '('+Lang("connected")+')'
            else:
                choiceName += '('+Lang("not connected")+')'

            choiceDefs.append(ChoiceDef(choiceName, lambda: self.HandleNICChoice(self.nicMenu.ChoiceIndex())))
        
        if len(choiceDefs) == 0:
            choiceDefs.append(ChoiceDef(Lang("<No interfaces present>"), None))
        else:
            choiceDefs.append(ChoiceDef(Lang("Disable Management Interface"), lambda: self.HandleNICChoice(None)))

        self.nicMenu = Menu(self, None, "Select Management NIC", choiceDefs)
        
        self.modeMenu = Menu(self, None, Lang("Select IP Address Configuration Mode"), [
            ChoiceDef(Lang("DHCP"), lambda: self.HandleModeChoice('DHCP') ), 
            ChoiceDef(Lang("Static"), lambda: self.HandleModeChoice('Static') ), 
            ])
        
        self.postDHCPMenu = Menu(self, None, Lang("Accept or Edit"), [
            ChoiceDef(Lang("Continue With DHCP Enabled"), lambda: self.HandlePostDHCPChoice('CONTINUE') ), 
            ChoiceDef(Lang("Convert to Static Addressing"), lambda: self.HandlePostDHCPChoice('CONVERT') ), 
            ])
        
        self.ChangeState('INITIAL')

        # Get best guess of current values
        self.mode = 'DHCP'
        self.IP = '0.0.0.0'
        self.netmask = '0.0.0.0'
        self.gateway = '0.0.0.0'
        if currentPIF is not None:
            if 'ip_configuration_mode' in currentPIF: self.mode = currentPIF['ip_configuration_mode']
            if self.mode.lower().startswith('static'):
                if 'IP' in currentPIF: self.IP = currentPIF['IP']
                if 'netmask' in currentPIF: self.netmask = currentPIF['netmask']
                if 'gateway' in currentPIF: self.gateway = currentPIF['gateway']
    
        # Make the menu current choices point to our best guess of current choices
        if self.nic is not None:
            self.nicMenu.CurrentChoiceSet(self.nic)
        if self.mode.lower().startswith('static'):
            self.modeMenu.CurrentChoiceSet(1)
        else:
            self.modeMenu.CurrentChoiceSet(0)
    
        self.ChangeState('INITIAL')
        self.UpdateFields()
        
    def BuildPane(self):
        pane = self.NewPane(DialoguePane(self.parent))
        pane.TitleSet(Lang("Management Interface Configuration"))
        pane.AddBox()
        
    def UpdateFieldsINITIAL(self):
        pane = self.Pane()
        pane.ResetFields()
        
        pane.AddTitleField(Lang("Select NIC for Management Interface"))
        pane.AddMenuField(self.nicMenu)
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK") } )

    def UpdateFieldsMODE(self):
        pane = self.Pane()
        pane.ResetFields()
        
        pane.AddTitleField(Lang("Select DHCP or static IP address configuration"))
        pane.AddMenuField(self.modeMenu)
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK") } )
        
    def UpdateFieldsSTATICIP(self):
        pane = self.Pane()
        pane.ResetFields()
        if self.converting:
            pane.AddTitleField(Lang("Please confirm or edit the static IP configuration"))
        else:
            pane.AddTitleField(Lang("Enter static IP address configuration"))
        pane.AddInputField(Lang("IP Address",  14),  self.IP, 'IP')
        pane.AddInputField(Lang("Netmask",  14),  self.netmask, 'netmask')
        pane.AddInputField(Lang("Gateway",  14),  self.gateway, 'gateway')
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK") } )
        
    def UpdateFieldsPRECOMMIT(self):
        pane = self.Pane()
        pane.ResetFields()
        
        pane.AddTitleField(Lang("Press <Enter> to apply the following configuration"))
        
        if self.nic is None:
            pane.AddWrappedTextField(Lang("The Management Interface will be disabled"))
        else:
            pif = Data.Inst().host.PIFs()[self.nic]
            pane.AddStatusField(Lang("Device",  16),  pif['device'])
            pane.AddStatusField(Lang("Name",  16),  pif['metrics']['device_name'])
            pane.AddStatusField(Lang("IP Mode",  16),  self.mode)
            if self.mode == 'Static':
                pane.AddStatusField(Lang("IP Address",  16),  self.IP)
                pane.AddStatusField(Lang("Netmask",  16),  self.netmask)
                pane.AddStatusField(Lang("Gateway",  16),  self.gateway)
                
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
        
    def UpdateFieldsPOSTDHCP(self):
        pane = self.Pane()
        pane.ResetFields()
   
        pane.AddWrappedBoldTextField(Lang("The following addresses have been assigned by DHCP.  Would you like to accept them and continue with DHCP enabled, or convert to a static configuration?"))
        pane.NewLine()
        
        if self.nic is None:
            pane.AddWrappedTextField(Lang("<No interface configured>"))
        else:
            pif = Data.Inst().host.PIFs()[self.nic]
            pane.AddStatusField(Lang("Device",  16),  pif['device'])
            pane.AddStatusField(Lang("Name",  16),  pif['metrics']['device_name'])
            pane.AddStatusField(Lang("IP Address",  16),  self.IP)
            pane.AddStatusField(Lang("Netmask",  16),  self.netmask)
            pane.AddStatusField(Lang("Gateway",  16),  self.gateway)
        pane.NewLine()
        pane.AddMenuField(self.postDHCPMenu)
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
        
    def UpdateFields(self):
        self.Pane().ResetPosition()
        getattr(self, 'UpdateFields'+self.state)() # Despatch method named 'UpdateFields'+self.state
    
    def ChangeState(self, inState):
        self.state = inState
        self.BuildPane()
        self.UpdateFields()
                            
    def HandleKeyINITIAL(self, inKey):
        return self.nicMenu.HandleKey(inKey)

    def HandleKeyMODE(self, inKey):
        return self.modeMenu.HandleKey(inKey)

    def HandleKeySTATICIP(self, inKey):
        handled = True
        pane = self.Pane()
        if inKey == 'KEY_ENTER':
            if pane.IsLastInput():
                inputValues = pane.GetFieldValues()
                self.IP = inputValues['IP']
                self.netmask = inputValues['netmask']
                self.gateway = inputValues['gateway']
                self.ChangeState('PRECOMMIT')
                self.UpdateFields()
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

    def HandleKeyPRECOMMIT(self, inKey):
        handled = True
        pane = self.Pane()
        if inKey == 'KEY_ENTER':
            Layout.Inst().TransientBanner( Lang("Reconfiguring network..."))
            try:
                self.Commit()
                if self.mode == 'DHCP':
                    data = Data.Inst()
                    self.IP = data.ManagementIP()
                    self.netmask = data.ManagementNetmask()
                    self.gateway = data.ManagementGateway()
                    self.ChangeState('POSTDHCP')

                else:
                    # Just report success for Static or None
                    Layout.Inst().PopDialogue()
                    Layout.Inst().PushDialogue(InfoDialogue( Lang("Configuration Successful")))
                
            except Exception, e:
                Layout.Inst().PopDialogue()
                Layout.Inst().PushDialogue(InfoDialogue( Lang("Configuration Failed: "+Lang(e))))
                
        else:
            handled = False
        return handled
    
    def HandleKeyPOSTDHCP(self, inKey):
        return self.postDHCPMenu.HandleKey(inKey)
    
    def HandleKey(self,  inKey):
        handled = False
        if hasattr(self, 'HandleKey'+self.state):
            handled = getattr(self, 'HandleKey'+self.state)(inKey)
        
        if not handled and inKey == 'KEY_ESCAPE':
            Layout.Inst().PopDialogue()
            handled = True

        return handled
            
    def HandleNICChoice(self,  inChoice):
        self.nic = inChoice
        if self.nic is None:
            self.ChangeState('PRECOMMIT')
        else:
            self.ChangeState('MODE')
        
    def HandleModeChoice(self,  inChoice):
        self.mode = inChoice
        if self.mode == 'DHCP':
            self.ChangeState('PRECOMMIT')
        else:
            self.ChangeState('STATICIP')
            self.Pane().InputIndexSet(0)
            
    def HandlePostDHCPChoice(self,  inChoice):
        if inChoice == 'CONTINUE':
            Layout.Inst().PopDialogue() # We're done
        elif inChoice == 'CONVERT':
            self.converting = True
            self.mode = 'Static'
            self.ChangeState('STATICIP')
            self.Pane().InputIndexSet(0)

    def Commit(self):
        data = Data.Inst()
        if self.nic is None:
            self.mode = None
            data.DisableManagement()
        else:
            pif = data.host.PIFs()[self.nic]
            if self.mode.lower().startswith('static'):
                # Comma-separated list of nameserver IPs
                dns = ','.join(data.dns.nameservers([]))
            else:
                dns = ''
            data.ReconfigureManagement(pif, self.mode, self.IP,  self.netmask, self.gateway, dns)
        
        data.Update()

class XSFeatureInterface(PlugIn):
    def __init__(self):
        PlugIn.__init__(self)
        
    @classmethod
    def StatusUpdateHandler(cls, inPane):
        data = Data.Inst()
        
        inPane.AddTitleField(Lang("Select Management Interface"))
        
        if len(data.derived.managementpifs([])) == 0:
            inPane.AddWrappedTextField(Lang("<No interface configured>"))
        else:
            for pif in data.derived.managementpifs([]):
                inPane.AddStatusField(Lang('Device', 16), pif['device'])
                inPane.AddStatusField(Lang('MAC Address', 16),  pif['MAC'])
                inPane.AddStatusField(Lang('DHCP/Static IP', 16),  pif['ip_configuration_mode'])

                inPane.AddStatusField(Lang('IP address', 16), data.ManagementIP(''))
                inPane.AddStatusField(Lang('Netmask', 16),  data.ManagementNetmask(''))
                inPane.AddStatusField(Lang('Gateway', 16),  data.ManagementGateway(''))
                
                inPane.NewLine()
                inPane.AddTitleField(Lang("NIC Vendor"))
                inPane.AddWrappedTextField(pif['metrics']['vendor_name'])
                inPane.NewLine()
                inPane.AddTitleField(Lang("NIC Model"))
                inPane.AddWrappedTextField(pif['metrics']['device_name'])
                
        inPane.AddKeyHelpField( {
            Lang("<Enter>") : Lang("Reconfigure"),
            Lang("<F5>") : Lang("Refresh")
        } )
    
    @classmethod
    def ActivateHandler(cls):
        DialogueUtils.AuthenticatedOnly(lambda: Layout.Inst().PushDialogue(InterfaceDialogue()))
        
    def Register(self):
        Importer.RegisterNamedPlugIn(
            self,
            'SELECT_MANAGEMENT_INTERFACE', # Key of this plugin for replacement, etc.
            {
                'title' : Lang('Select Management NIC'), # Name of this plugin for plugin list
                'menuname' : 'MENU_MANAGEMENT',
                'menupriority' : 150,
                'menutext' : Lang('Select Management NIC') ,
                'needsauth' : True,
                'statusupdatehandler' : XSFeatureInterface.StatusUpdateHandler,
                'activatehandler' : XSFeatureInterface.ActivateHandler
            }
        )

# Register this plugin when module is imported
XSFeatureInterface().Register()
