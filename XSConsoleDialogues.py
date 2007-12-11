# Copyright (c) Citrix Systems 2007. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

from XSConsoleAuth import *
from XSConsoleBases import *
from XSConsoleCurses import *
from XSConsoleData import *
from XSConsoleDataUtils import *
from XSConsoleDialoguePane import *
from XSConsoleFields import *
from XSConsoleLang import *
from XSConsoleMenus import *
from XSConsoleUtils import *

class LoginDialogue(Dialogue):
    def __init__(self, inLayout, inParent,  inText = None,  inSuccessFunc = None):
        Dialogue.__init__(self, inLayout, inParent)
        self.text = inText
        self.successFunc = inSuccessFunc
        if self.text is None:
            paneHeight = 7
        else:
            paneHeight = 9
        pane = self.NewPane('login', DialoguePane(3, 12 - paneHeight/2, 74, paneHeight, self.parent))
        pane.ColoursSet('MODAL_BASE', 'MODAL_BRIGHT', 'MODAL_HIGHLIGHT')
        pane.Win().TitleSet("Login")
        pane.AddBox()
        self.UpdateFields()
        pane.InputIndexSet(0)
        
    def UpdateFields(self):
        pane = self.Pane('login')
        pane.ResetFields()
        if self.text is not None:
            pane.AddTitleField(self.text)
        pane.AddInputField(Lang("Username", 14), "root", 'username')
        pane.AddPasswordField(Lang("Password", 14), Auth.Inst().DefaultPassword(), 'password')
        pane.AddKeyHelpField( {
            Lang("<Esc>") : Lang("Cancel"),
            Lang("<Enter>") : Lang("Next/OK"),
            Lang("<Tab>") : Lang("Next")
        })
        
    def HandleKey(self, inKey):
        handled = True
        pane = self.Pane('login')
        if inKey == 'KEY_ESCAPE':
            self.layout.PopDialogue()
        elif inKey == 'KEY_ENTER':
            if not pane.IsLastInput():
                pane.ActivateNextInput()
            else:
                inputValues = pane.GetFieldValues()
                self.layout.PopDialogue()
                self.layout.DoUpdate() # Redraw now as login can take a while
                try:
                    Auth.Inst().ProcessLogin(inputValues['username'], inputValues['password'])

                    if self.successFunc is not None:
                        self.successFunc()
                    else:
                        self.layout.PushDialogue(InfoDialogue(self.layout, self.parent, Lang('Login Successful')))
                
                except Exception, e:
                    self.layout.PushDialogue(InfoDialogue(self.layout, self.parent, Lang('Login Failed: ')+Lang(e)))

                Data.Inst().Update()
                
        elif inKey == 'KEY_TAB':
            pane.ActivateNextInput()
        elif inKey == 'KEY_BTAB':
            pane.ActivatePreviousInput()
        elif pane.CurrentInput().HandleKey(inKey):
            pass # Leave handled as True
        else:
            handled = False
        return handled

class ChangePasswordDialogue(Dialogue):
    def __init__(self, inLayout, inParent,  inText = None,  inSuccessFunc = None):
        Dialogue.__init__(self, inLayout, inParent)
        self.text = inText
        self.successFunc = inSuccessFunc
        self.isPasswordSet = Auth.Inst().IsPasswordSet()
            
        if self.text is None:
            paneHeight = 7
        else:
            paneHeight = 9
            
        if self.isPasswordSet:
            paneHeight += 1 # For old password field
            
        pane = self.NewPane('changepassword', DialoguePane(3, 12 - paneHeight/2, 74, paneHeight, self.parent))
        pane.ColoursSet('MODAL_BASE', 'MODAL_BRIGHT', 'MODAL_HIGHLIGHT')
        pane.Win().TitleSet("Change Password")
        pane.AddBox()
        self.UpdateFields()
        pane.InputIndexSet(0)
        
    def UpdateFields(self):
        pane = self.Pane('changepassword')
        pane.ResetFields()
        if self.text is not None:
            pane.AddTitleField(self.text)
        if self.isPasswordSet:
            pane.AddPasswordField(Lang("Old Password", 21), Auth.Inst().DefaultPassword(), 'oldpassword')
        pane.AddPasswordField(Lang("New Password", 21), Auth.Inst().DefaultPassword(), 'newpassword1')
        pane.AddPasswordField(Lang("Repeat New Password", 21), Auth.Inst().DefaultPassword(), 'newpassword2')
        pane.AddKeyHelpField( {
            Lang("<Enter>") : Lang("Next/OK"),
            Lang("<Esc>") : Lang("Cancel"),
            Lang("<Tab>") : Lang("Next")
        })
        
    def HandleKey(self, inKey):
        handled = True
        pane = self.Pane('changepassword')
        if inKey == 'KEY_ESCAPE':
            self.layout.PopDialogue()
        elif inKey == 'KEY_ENTER':
            if not pane.IsLastInput():
                pane.ActivateNextInput()
            else:
                inputValues = pane.GetFieldValues()
                self.layout.PopDialogue()
                successMessage = Lang('Password Change Successful')
                try:
                    if not Auth.Inst().IsAuthenticated() and self.isPasswordSet:
                        # Log in automatically if we're not
                        Auth.Inst().ProcessLogin('root', inputValues.get('oldpassword', ''))
                        successMessage += Lang(".  User 'root' logged in.")
                        
                    if inputValues['newpassword1'] != inputValues['newpassword2']:
                        raise Exception(Lang('New passwords do not match'))
                
                    Auth.Inst().ChangePassword(inputValues.get('oldpassword', ''), inputValues['newpassword1'])
                    
                except Exception, e:
                    self.layout.PushDialogue(InfoDialogue(self.layout, self.parent,
                        Lang('Password Change Failed: ')+Lang(e)))
                    
                else:
                    self.layout.PushDialogue(InfoDialogue(self.layout, self.parent, successMessage))
                    State.Inst().PasswordChangeRequiredSet(False)
                    
                Data.Inst().Update()

        elif inKey == 'KEY_TAB':
            pane.ActivateNextInput()
        elif inKey == 'KEY_BTAB':
            pane.ActivatePreviousInput()
        elif pane.CurrentInput().HandleKey(inKey):
            pass # Leave handled as True
        else:
            handled = False
        return True

class InfoDialogue(Dialogue):
    def __init__(self, inLayout, inParent, inText,  inInfo = None):
        Dialogue.__init__(self, inLayout, inParent)
        self.text = inText
        self.info = inInfo
        
        if inInfo is None:
            paneHeight = 5 + len(Language.ReflowText(self.text, 70))
        else:
            paneHeight = 7 + len(Language.ReflowText(self.info, 70))
                
        paneHeight = min(paneHeight,  22)
        
        pane = self.NewPane('info', DialoguePane(3, 12 - paneHeight/2, 74, paneHeight, self.parent))
        pane.ColoursSet('MODAL_BASE', 'MODAL_BRIGHT', 'MODAL_HIGHLIGHT')
        pane.AddBox()
        self.UpdateFields()

    def UpdateFields(self):
        pane = self.Pane('info')
        pane.ResetFields()
        if len(self.text) < 70:
            # Centre text if short
            pane.ResetPosition(37 - len(self.text) / 2, 1)
        else:
            pane.ResetPosition(1, 1)
        
        pane.AddWrappedBoldTextField(self.text)
        if self.info is not None:
            pane.ResetPosition(1, 3)
            pane.AddWrappedTextField(self.info)
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK") } )
        
    def HandleKey(self, inKey):
        handled = True
        if inKey == 'KEY_ESCAPE' or inKey == 'KEY_ENTER':
            self.layout.PopDialogue()
        else:
            handled = False
        return True

class BannerDialogue(Dialogue):
    def __init__(self, inLayout, inParent, inText):
        Dialogue.__init__(self, inLayout, inParent)
        self.text = inText
        paneHeight = 4 + len(Language.ReflowText(self.text, 70))
        paneHeight = min(paneHeight,  22)
        pane = self.NewPane('banner', DialoguePane(3, 12 - paneHeight/2, 74, paneHeight, self.parent))
        pane.ColoursSet('MODAL_BASE', 'MODAL_BRIGHT', 'MODAL_HIGHLIGHT')
        pane.AddBox()
        self.UpdateFields()

    def UpdateFields(self):
        pane = self.Pane('banner')
        pane.ResetFields()
        if len(self.text) < 70:
            # Centre text if short
            pane.ResetPosition(37 - len(self.text) / 2, 1)
        else:
            pane.ResetPosition(1, 1)
        
        pane.AddWrappedBoldTextField(self.text)

class QuestionDialogue(Dialogue):
    def __init__(self, inLayout, inParent, inText,  inHandler):
        Dialogue.__init__(self, inLayout, inParent)
        self.text = inText
        self.handler = inHandler
        paneHeight = 5 + len(Language.ReflowText(self.text, 70))
        paneHeight = min(paneHeight,  22)
        pane = self.NewPane('question', DialoguePane(3, 12 - paneHeight/2, 74, paneHeight, self.parent))
        pane.ColoursSet('MODAL_BASE', 'MODAL_BRIGHT', 'MODAL_HIGHLIGHT')
        pane.AddBox()
        self.UpdateFields()

    def UpdateFields(self):
        pane = self.Pane('question')
        pane.ResetFields()
        if len(self.text) < 70:
            # Centre text if short
            pane.ResetPosition(37 - len(self.text) / 2, 1)
        else:
            pane.ResetPosition(1, 1)
        
        pane.AddWrappedBoldTextField(self.text)

        pane.AddKeyHelpField( { Lang("<F8>") : Lang("Yes"),  Lang("<Esc>") : Lang("No")  } )
    
    def HandleKey(self, inKey):
        handled = True
        if inKey == 'y' or inKey == 'Y' or inKey == 'KEY_F(8)':
            self.layout.PopDialogue()
            self.handler('y')
        elif inKey == 'n' or inKey == 'N' or inKey == 'KEY_ESCAPE':
            self.layout.PopDialogue()
            self.handler('n')
        else:
            handled = False
            
        return handled

class InterfaceDialogue(Dialogue):
    def __init__(self, inLayout, inParent):
        Dialogue.__init__(self, inLayout, inParent)
        numNICs = len(Data.Inst().host.PIFs([]))
        paneHeight = max(numNICs,  5) + 6
        paneHeight = min(paneHeight,  22)
        pane = self.NewPane('interface', DialoguePane(3, 12 - paneHeight/2, 74, paneHeight, self.parent))
        pane.ColoursSet('MODAL_BASE', 'MODAL_BRIGHT', 'MODAL_MENU_HIGHLIGHT')
        pane.Win().TitleSet(Lang("Management Interface Configuration"))
        pane.AddBox()
        
        choiceDefs = []

        self.nic=0
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
            choiceDefs.append(ChoiceDef(Lang("None"), lambda: self.HandleNICChoice(None)))

        self.nicMenu = Menu(self, None, "Select Management NIC", choiceDefs)
        
        self.modeMenu = Menu(self, None, Lang("Select IP Address Configuration Mode"), [
            ChoiceDef(Lang("DHCP"), lambda: self.HandleModeChoice('DHCP') ), 
            ChoiceDef(Lang("Static"), lambda: self.HandleModeChoice('Static') ), 
            ])
        
        self.state = 'INITIAL'

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
    
        self.UpdateFields()
        
    def UpdateFieldsINITIAL(self):
        pane = self.Pane('interface')
        pane.ResetFields()
        
        pane.AddTitleField(Lang("Select NIC for management interface"))
        pane.AddMenuField(self.nicMenu)
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK") } )

    def UpdateFieldsMODE(self):
        pane = self.Pane('interface')
        pane.ResetFields()
        
        pane.AddTitleField(Lang("Select DHCP or Static IP Address Configuration"))
        pane.AddMenuField(self.modeMenu)
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK") } )
        
    def UpdateFieldsSTATICIP(self):
        pane = self.Pane('interface')
        pane.ResetFields()
        pane.ColoursSet('MODAL_BASE', 'MODAL_BRIGHT', 'MODAL_HIGHLIGHT')
        pane.AddTitleField(Lang("Enter Static IP Address Configuration"))
        pane.AddInputField(Lang("IP Address",  14),  self.IP, 'IP')
        pane.AddInputField(Lang("Netmask",  14),  self.netmask, 'netmask')
        pane.AddInputField(Lang("Gateway",  14),  self.gateway, 'gateway')
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK") } )
        
    def UpdateFieldsPRECOMMIT(self):
        pane = self.Pane('interface')
        pane.ResetFields()
        if self.nic is None:
            pane.AddTextField(Lang("No management interface will be configured"))
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
        
    def UpdateFields(self):
        self.Pane('interface').ResetPosition()
        getattr(self, 'UpdateFields'+self.state)() # Despatch method named 'UpdateFields'+self.state
    
    def HandleKeyINITIAL(self, inKey):
        return self.nicMenu.HandleKey(inKey)

    def HandleKeyMODE(self, inKey):
        return self.modeMenu.HandleKey(inKey)

    def HandleKeySTATICIP(self, inKey):
        handled = True
        pane = self.Pane('interface')
        if inKey == 'KEY_ENTER':
            if pane.IsLastInput():
                inputValues = pane.GetFieldValues()
                self.IP = inputValues['IP']
                self.netmask = inputValues['netmask']
                self.gateway = inputValues['gateway']
                self.state = 'PRECOMMIT'
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
        pane = self.Pane('interface')
        if inKey == 'KEY_ENTER':
            self.layout.PopDialogue()
            self.layout.PushDialogue(BannerDialogue(self.layout, self.parent, Lang("Reconfiguring network...")))
            self.layout.Refresh()
            self.layout.DoUpdate()
            try:
                self.Commit()
                self.layout.PopDialogue()
                self.layout.PushDialogue(InfoDialogue(self.layout, self.parent, Lang("Configuration Successful")))
                
            except Exception, e:
                self.layout.PopDialogue()
                self.layout.PushDialogue(InfoDialogue(self.layout, self.parent, Lang("Configuration Failed: "+Lang(e))))
                
        else:
            handled = False
        return handled
        
    def HandleKey(self,  inKey):
        handled = False
        if hasattr(self, 'HandleKey'+self.state):
            handled = getattr(self, 'HandleKey'+self.state)(inKey)
        
        if not handled and inKey == 'KEY_ESCAPE':
            self.layout.PopDialogue()
            handled = True

        return handled
            
    def HandleNICChoice(self,  inChoice):
        self.nic = inChoice
        if self.nic is None:
            self.state = 'PRECOMMIT'
        else:
            self.state = 'MODE'
        self.UpdateFields()
        
    def HandleModeChoice(self,  inChoice):
        self.mode = inChoice
        if self.mode == 'DHCP':
            self.state = 'PRECOMMIT'
            self.UpdateFields()
        else:
            self.state = 'STATICIP'
            self.UpdateFields() # Setup input fields first
            self.Pane('interface').InputIndexSet(0) # and then choose the first
            
    def Commit(self):
        if self.nic is None:
            pass # TODO: Delete interfaces
        else:
            data = Data.Inst()
            pif = data.host.PIFs()[self.nic]
            if self.mode.lower().startswith('static'):
                # Comma-separated list of nameserver IPs
                dns = ','.join(data.dns.nameservers([]))
            else:
                dns = ''
            data.ReconfigureManagement(pif, self.mode, self.IP,  self.netmask, self.gateway, dns)
            Data.Inst().Update()
            
class DNSDialogue(Dialogue):
    def __init__(self, inLayout, inParent):
        Dialogue.__init__(self, inLayout, inParent)
        data=Data.Inst()
        paneHeight = 10
        pane = self.NewPane('dns', DialoguePane(3, 12 - paneHeight/2, 74, paneHeight, self.parent))
        pane.ColoursSet('MODAL_BASE', 'MODAL_BRIGHT', 'MODAL_MENU_HIGHLIGHT')
        pane.Win().TitleSet(Lang("DNS Configuration"))
        pane.AddBox()
        
        choiceDefs = [
            ChoiceDef(Lang("Add a nameserver"), lambda: self.HandleAddRemoveChoice('ADD') ) ]
        
        if len(data.dns.nameservers([])) > 0:
            choiceDefs.append(ChoiceDef(Lang("Remove a single nameserver"), lambda: self.HandleAddRemoveChoice('REMOVE') ))
            choiceDefs.append(ChoiceDef(Lang("Remove all nameservers"), lambda: self.HandleAddRemoveChoice('REMOVEALL') ))
        
        self.addRemoveMenu = Menu(self, None, Lang("Add or Remove Nameserver Entries"), choiceDefs)
        
        choiceDefs = []
        
        for server in Data.Inst().dns.nameservers([]):
            choiceDefs.append(ChoiceDef(server, lambda: self.HandleRemoveChoice(self.removeMenu.ChoiceIndex())))
        
        self.removeMenu = Menu(self, None, Lang("Remove Nameserver Entry"), choiceDefs)
        
        self.state = 'INITIAL'

        self.UpdateFields()
        
    def UpdateFieldsINITIAL(self):
        pane = self.Pane('dns')
        pane.ResetFields()
        
        pane.AddTitleField(Lang("Add or Remove Nameserver Entries"))
        pane.AddMenuField(self.addRemoveMenu)
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK") } )
    
    def UpdateFieldsADD(self):
        pane = self.Pane('dns')
        pane.ColoursSet('MODAL_BASE', 'MODAL_BRIGHT', 'MODAL_HIGHLIGHT')
        pane.ResetFields()
        
        pane.AddTitleField(Lang("Please Enter the Nameserver IP Address"))
        pane.AddInputField(Lang("IP Address", 16),'0.0.0.0', 'address')
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK") , Lang("<Esc>") : Lang("Cancel") } )
        if pane.CurrentInput() is None:
            pane.InputIndexSet(0)

    def UpdateFieldsREMOVE(self):
        pane = self.Pane('dns')
        pane.ResetFields()
        
        pane.AddTitleField(Lang("Select Nameserver Entry To Remove"))
        pane.AddMenuField(self.removeMenu)
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK") , Lang("<Esc>") : Lang("Cancel") } )
        
    def UpdateFields(self):
        self.Pane('dns').ResetPosition()
        getattr(self, 'UpdateFields'+self.state)() # Despatch method named 'UpdateFields'+self.state
    
    def HandleKeyINITIAL(self, inKey):
        return self.addRemoveMenu.HandleKey(inKey)
     
    def HandleKeyADD(self, inKey):
        handled = True
        pane = self.Pane('dns')
        if pane.CurrentInput() is None:
            pane.InputIndexSet(0)
        if inKey == 'KEY_ENTER':
            inputValues = pane.GetFieldValues()
            self.layout.PopDialogue()
            data=Data.Inst()
            servers = data.dns.nameservers([])
            servers.append(inputValues['address'])
            data.NameserversSet(servers)
            self.Commit(Lang("Nameserver")+" "+inputValues['address']+" "+Lang("added"))
        elif pane.CurrentInput().HandleKey(inKey):
            pass # Leave handled as True
        else:
            handled = False
        return handled

    def HandleKeyREMOVE(self, inKey):
        return self.removeMenu.HandleKey(inKey)
        
    def HandleKey(self,  inKey):
        handled = False
        if hasattr(self, 'HandleKey'+self.state):
            handled = getattr(self, 'HandleKey'+self.state)(inKey)
        
        if not handled and inKey == 'KEY_ESCAPE':
            self.layout.PopDialogue()
            handled = True

        return handled
            
    def HandleAddRemoveChoice(self,  inChoice):
        if inChoice == 'ADD':
            self.state = 'ADD'
            self.UpdateFields()
        elif inChoice == 'REMOVE':
            self.state = 'REMOVE'
            self.UpdateFields()
        elif inChoice == 'REMOVEALL':
            self.layout.PopDialogue()
            Data.Inst().NameserversSet([])
            self.Commit(Lang("All nameserver entries deleted"))

    def HandleRemoveChoice(self,  inChoice):
        self.layout.PopDialogue()
        data=Data.Inst()
        servers = data.dns.nameservers([])
        thisServer = servers[inChoice]
        del servers[inChoice]
        data.NameserversSet(servers)
        self.Commit(Lang("Nameserver")+" "+thisServer+" "+Lang("deleted"))
    
    def Commit(self, inMessage):
        try:
            Data.Inst().SaveToResolvConf()
            self.layout.PushDialogue(InfoDialogue(self.layout, self.parent, inMessage))
        except Exception, e:
            self.layout.PushDialogue(InfoDialogue(self.layout, self.parent, Lang("Update failed: ")+Lang(e)))

class InputDialogue(Dialogue):
    def __init__(self, inLayout, inParent):
        Dialogue.__init__(self, inLayout, inParent)
        if self.Custom('info') is None:
            paneHeight = 5
        else:
            paneHeight = 6+len(Language.ReflowText(self.Custom('info'), 70))
        paneHeight += len(self.Custom('fields'))
        paneHeight = min(paneHeight, 22)
        pane = self.NewPane('input', DialoguePane(3, 12 - paneHeight/2, 74, paneHeight, self.parent))
        pane.ColoursSet('MODAL_BASE', 'MODAL_BRIGHT', 'MODAL_HIGHLIGHT')
        pane.Win().TitleSet(self.Custom('title'))
        pane.AddBox()
        self.UpdateFields()
        pane.InputIndexSet(0)
    
    def Custom(self, inKey):
        return self.custom.get(inKey, None)
    
    def UpdateFields(self):
        pane = self.Pane('input')
        pane.ResetFields()
        if self.Custom('info') is not None:
            pane.AddWrappedTextField(self.Custom('info'))
            pane.NewLine()
            
        for field in self.Custom('fields'):
            pane.AddInputField(*field)
        
        pane.AddKeyHelpField( {
            Lang("<Enter>") : Lang("OK"),
            Lang("<Esc>") : Lang("Cancel")
        })
    
    def HandleCommit(self, inValues): # Override this
        self.layout.PopDialogue()
    
    def HandleKey(self, inKey):
        handled = True
        pane = self.Pane('input')
        if inKey == 'KEY_ESCAPE':
            self.layout.PopDialogue()
        elif inKey == 'KEY_ENTER':
            if not pane.IsLastInput():
                pane.ActivateNextInput()
            else:
                try:
                    self.layout.PopDialogue()
                    self.layout.DoUpdate()
                    title, info = self.HandleCommit(self.Pane('input').GetFieldValues())
                    self.layout.PushDialogue(InfoDialogue(self.layout, self.parent, title, info))
                except Exception, e:
                    self.layout.PushDialogue(InfoDialogue(self.layout, self.parent, Lang('Failed: ')+Lang(e)))
        elif inKey == 'KEY_TAB':
            pane.ActivateNextInput()
        elif inKey == 'KEY_BTAB': # BTAB not available on all platforms
            pane.ActivatePreviousInput()
        elif pane.CurrentInput().HandleKey(inKey):
            pass # Leave handled as True
        else:
            handled = False
        return True

class HostnameDialogue(InputDialogue):
    def __init__(self, inLayout, inParent):
        self.custom = {
            'title' : Lang("Change Hostname"),
            'fields' : [ [Lang("Hostname", 14), Data.Inst().host.name_label(''), 'hostname'] ]
            }
        InputDialogue.__init__(self, inLayout, inParent)

    def HandleCommit(self, inValues):
        Data.Inst().HostnameSet(inValues['hostname'])
        Data.Inst().Update()
        return Lang('Hostname Change Successful'), Lang("Hostname changed to '")+inValues['hostname']+"'"

class ChangeTimeoutDialogue(InputDialogue):
    def __init__(self, inLayout, inParent):
        self.custom = {
            'title' : Lang("Change Auto-Logout Timeout"),
            'fields' : [ [Lang("Timeout (minutes)", 20), 5, 'timeout'] ]
            }
        InputDialogue.__init__(self, inLayout, inParent)

    def HandleCommit(self, inValues):
        timeoutMinutes = int(inValues['timeout'])
        Auth.Inst().TimeoutSecondsSet(timeoutMinutes * 60)
        return Lang('Timeout Change Successful'), Lang("Timeout changed to ")+inValues['timeout']+Language.Quantity(" minute",  timeoutMinutes)+'.'
        
class BugReportDialogue(InputDialogue):
    def __init__(self, inLayout, inParent):
        self.custom = {
            'title' : Lang("Upload Bug Report"),
            'info' : Lang("Please confirm the ftp destination and enter a proxy name if required (or blank for none)"), 
            'fields' : [
                [Lang("Destination", 20), Config.Inst().FTPServer(), 'destination'],
                [Lang("Proxy", 20), '', 'proxy']
            ]
        }
        InputDialogue.__init__(self, inLayout, inParent)

    def HandleCommit(self, inValues):
        self.layout.PushDialogue(BannerDialogue(self.layout, self.parent, Lang("Uploading Bug Report...")))
        self.layout.Refresh()
        self.layout.DoUpdate()
        
        hostRef = ShellUtils.MakeSafeParam(Data.Inst().host.uuid(''))
        destURL = ShellUtils.MakeSafeParam(inValues['destination'])
        proxy = ShellUtils.MakeSafeParam(inValues['proxy'])
        
        command = "/opt/xensource/bin/xe host-bugreport-upload host='"+hostRef+"' url='"+destURL+"'"
        if proxy != '':
            command += " http_proxy='"+proxy+"'"
            
        status, output = commands.getstatusoutput(command)
        
        self.layout.PopDialogue()
                
        if status != 0:
            raise Exception(output) 

        return Lang("Bug Report Uploaded Sucessfully")
        
class SyslogDialogue(InputDialogue):
    def __init__(self, inLayout, inParent):
        self.custom = {
            'title' : Lang("Change Logging Destination"),
            'info' : Lang("Please enter the hostname or IP address for remote logging (or blank for none)"), 
            'fields' : [ [Lang("Destination", 20), Data.Inst().host.logging.syslog_destination(''), 'destination'] ]
            }
        InputDialogue.__init__(self, inLayout, inParent)

    def HandleCommit(self, inValues):
        self.layout.PushDialogue(BannerDialogue(self.layout, self.parent, Lang("Setting Logging Destination...")))
        self.layout.Refresh()
        self.layout.DoUpdate()
        
        Data.Inst().LoggingDestinationSet(inValues['destination'])
        Data.Inst().Update()
        
        self.layout.PopDialogue()
        
        if inValues['destination'] == '':
            message = Lang("Remote logging disabled.")
        else:
            message = Lang("Logging destination set to '")+inValues['destination'] + "'."
        return Lang('Logging Destination Change Successful'), message        

class SRDialogue(Dialogue):
    def __init__(self, inLayout, inParent):
        Dialogue.__init__(self, inLayout, inParent)

        self.deviceToErase = None
        self.ChangeState('INITIAL')

    def DeviceString(self, inDevice):
        retVal = "%-6.6s%-44.44s%-10.10s%10.10s" % (
            FirstValue(inDevice.bus[:6], ''),
            FirstValue(inDevice.name[:50], ''),
            FirstValue(inDevice.device[:10], ''),
            FirstValue(FileUtils.SizeString(inDevice.size), '')
        )
        return retVal
        
    def BuildPaneBase(self, inHeight):
        paneHeight = min(inHeight,  22)
        pane = self.NewPane('sr', DialoguePane(3, 12 - paneHeight/2, 74, paneHeight, self.parent))
        pane.Win().TitleSet(Lang("Claim Disk As Storage Repository"))
        pane.AddBox()
    
    def BuildPaneINITIAL(self):
        self.BuildPaneBase(9)
        self.UpdateFields()
        
    def BuildPaneDEVICE(self):
        self.deviceList = FileUtils.SRDeviceList()
        
        self.BuildPaneBase(8+len(self.deviceList))
        
        choiceDefs = []
        for device in self.deviceList:
            choiceDefs.append(ChoiceDef(self.DeviceString(device), lambda: self.HandleDeviceChoice(self.deviceMenu.ChoiceIndex()) ) )
        
        if len(choiceDefs) == 0:
            choiceDefs.append(ChoiceDef(Lang("<No devices available>", 70), None))
    
        # Manual choice disabled    
        # choiceDefs.append(ChoiceDef(Lang("Specify a device manually", 70), lambda: self.HandleDeviceChoice(None) ) )

        self.deviceMenu = Menu(self, None, Lang("Select Device"), choiceDefs)
        self.UpdateFields()

    def BuildPaneCUSTOM(self):
        self.BuildPaneBase(11)
        self.UpdateFields()
        
    def BuildPaneCONFIRM(self):
        self.BuildPaneBase(11)
        self.UpdateFields()
    
    def ChangeState(self, inState):
        self.state = inState
        getattr(self, 'BuildPane'+self.state)() # Despatch method named 'BuildPane'+self.state
    
    def UpdateFields(self):
        self.Pane('sr').ResetPosition()
        getattr(self, 'UpdateFields'+self.state)() # Despatch method named 'UpdateFields'+self.state
        
    def UpdateFieldsINITIAL(self):
        pane = self.Pane('sr')
        pane.ColoursSet('MODAL_BASE', 'MODAL_FLASH', 'MODAL_HIGHLIGHT')
        pane.ResetFields()
        
        pane.AddTitleField(Lang("WARNING"))
        pane.ColoursSet('MODAL_BASE', 'MODAL_BRIGHT', 'MODAL_HIGHLIGHT')
        pane.AddWrappedTextField(Lang("Once a disk is selected, this function will erase all information on that disk.  Do you want to continue?"))
        pane.AddKeyHelpField( { Lang("<F8>") : Lang("Continue"), Lang("<Esc>") : Lang("Cancel") } )

    def UpdateFieldsDEVICE(self):
        pane = self.Pane('sr')
        pane.ColoursSet('MODAL_BASE', 'MODAL_BRIGHT', 'MODAL_MENU_HIGHLIGHT')
        pane.ResetFields()
        
        pane.AddTitleField(Lang("Select a disk to erase and claim as a storage repository."))
        pane.AddMenuField(self.deviceMenu)
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel"), 
            "<F5>" : Lang("Rescan") } )

    def UpdateFieldsCUSTOM(self):
        pane = self.Pane('sr')
        pane.ColoursSet('MODAL_BASE', 'MODAL_BRIGHT', 'MODAL_HIGHLIGHT')
        pane.ResetFields()
        
        pane.AddTitleField(Lang("Enter the device name, e.g. /dev/sdb"))
        pane.AddInputField(Lang("Device Name",  16), '', 'device')
        pane.NewLine()
        pane.AddWrappedTextField(Lang("WARNING: No checks will be performed on this device before it is erased."))
        
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Exit") } )
        if pane.CurrentInput() is None:
            pane.InputIndexSet(0)
            
    def UpdateFieldsCONFIRM(self):
        pane = self.Pane('sr')
        pane.ColoursSet('MODAL_BASE', 'MODAL_BRIGHT', 'MODAL_HIGHLIGHT')
        pane.ResetFields()
        
        pane.AddWrappedBoldTextField(Lang("Press <F8> to confirm that you want to erase all information on this disk and use it as a storage repository.  Data currently on this disk cannot be recovered after this step."))
        pane.NewLine()
        pane.AddWrappedBoldTextField(Lang("Device"))
        if isinstance(self.deviceToErase, Struct):
            pane.AddWrappedTextField(self.DeviceString(self.deviceToErase))
        else:
            pane.AddWrappedTextField(str(self.deviceToErase))

        pane.AddKeyHelpField( { Lang("<F8>") : Lang("Erase and Claim"), Lang("<Esc>") : Lang("Cancel") } )

    def HandleKey(self, inKey):
        handled = False
        if hasattr(self, 'HandleKey'+self.state):
            handled = getattr(self, 'HandleKey'+self.state)(inKey)
        
        if not handled and inKey == 'KEY_ESCAPE':
            self.layout.PopDialogue()
            handled = True

        return handled
        
    def HandleKeyINITIAL(self, inKey):
        handled = False
        
        if inKey == 'KEY_F(8)':
            self.layout.PushDialogue(BannerDialogue(self.layout, self.parent, Lang("Scanning...")))
            self.layout.Refresh()
            self.layout.DoUpdate()
            self.layout.PopDialogue()
            self.ChangeState('DEVICE')
            handled = True
            
        return handled

    def HandleKeyDEVICE(self, inKey):
        handled = self.deviceMenu.HandleKey(inKey)
        
        if not handled and inKey == 'KEY_F(5)':
            self.layout.PushDialogue(BannerDialogue(self.layout, self.parent, Lang("Rescanning...")))
            self.layout.Refresh()
            self.layout.DoUpdate()
            self.layout.PopDialogue()
            self.BuildPaneDEVICE() # Updates self.deviceList
            time.sleep(0.5) # Display rescanning box for a reasonable time
            self.layout.Refresh()
            handled = True
            
        return handled
    
    def HandleKeyCUSTOM(self, inKey):
        handled = True
        pane = self.Pane('sr')
        if pane.CurrentInput() is None:
            pane.InputIndexSet(0)
        if inKey == 'KEY_ENTER':
            inputValues = pane.GetFieldValues()
            self.deviceToErase = inputValues['device']
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
    
    def HandleDeviceChoice(self, inChoice):
        if inChoice is None:
            self.ChangeState('CUSTOM')
        else:
            self.deviceToErase = self.deviceList[inChoice]
    
            self.ChangeState('CONFIRM')

    def DoAction(self):
        if isinstance(self.deviceToErase, Struct):
            deviceName = self.deviceToErase.device
        else:
            deviceName = str(self.deviceToErase)
        
        self.layout.ExitBannerSet(Lang("Configuring Storage Repository"))
        self.layout.SubshellCommandSet("/opt/xensource/bin/diskprep -f "+deviceName +" && sleep 4")
        State.Inst().RebootMessageSet(Lang("This server must reboot to use the new storage repository.  Reboot the server now?"))

class RemoteDBDialogue(Dialogue):
    def __init__(self, inLayout, inParent):
        Dialogue.__init__(self, inLayout, inParent)

        self.useMenu = Menu(self, None, Lang("Choose Option"), [
            ChoiceDef(Lang("Use existing database"), lambda: self.HandleUseChoice('USE')),
            ChoiceDef(Lang("Format disk and create new database"), lambda: self.HandleUseChoice('FORMAT')),
            ChoiceDef(Lang("Cancel"), lambda: self.HandleUseChoice('CANCEL'))
        ] )            
            
        self.ChangeState('INITIAL')

    def IQNString(self, inIQN, inLUN = None):
        if inLUN is None or int(inLUN) > 999: # LUN not present or more than 3 characters
            retVal = "TGPT %-4.4s %-60.60s" % (inIQN.tgpt[:4], inIQN.name[:60])
        else:
            retVal = "TGPT %-4.4s %-52.52s LUN %-3.3s" % (inIQN.tgpt[:4], inIQN.name[:52], str(inLUN)[:3])
        
        return retVal

    def BuildPaneBase(self, inHeight):
        paneHeight = min(inHeight, 22)
        pane = self.NewPane('remotedb', DialoguePane(3, 12 - paneHeight/2, 74, paneHeight, self.parent))
        pane.Win().TitleSet(Lang("Remote Database Configuration"))
        pane.AddBox()
    
    def BuildPaneINITIAL(self):
        self.BuildPaneBase(14)
        self.UpdateFields()
    
    def BuildPaneCHOOSEIQN(self):
        self.BuildPaneBase(7+len(self.probedIQNs))

        choiceDefs = []
        
        for iqn in self.probedIQNs:
            choiceDefs.append(ChoiceDef(self.IQNString(iqn), lambda: self.HandleIQNChoice(self.iqnMenu.ChoiceIndex())))

        if len(choiceDefs) == 0:
            choiceDefs.append(ChoiceDef("<No IQNs discovered>", lambda: None))
            
        self.iqnMenu = Menu(self, None, Lang("Select IQN"), choiceDefs)

        self.UpdateFields()

    def BuildPaneCHOOSELUN(self):
        self.BuildPaneBase(7+len(self.probedLUNs))

        choiceDefs = []
        
        for lun in self.probedLUNs:
            choiceDefs.append(ChoiceDef("LUN "+str(lun), lambda: self.HandleLUNChoice(self.lunMenu.ChoiceIndex())))

        if len(choiceDefs) == 0:
            choiceDefs.append(ChoiceDef("<No LUNs discovered>", lambda: None))
            
        self.lunMenu = Menu(self, None, Lang("Select LUN"), choiceDefs)

        self.UpdateFields()

    def BuildPaneCREATEDB(self):
        self.BuildPaneBase(11)
        self.UpdateFields()
        
    def BuildPaneUSEDB(self):
        self.BuildPaneBase(14)
        self.UpdateFields()
    
    def ChangeState(self, inState):
        self.state = inState
        getattr(self, 'BuildPane'+self.state)() # Despatch method named 'BuildPane'+self.state
        
    def UpdateFieldsINITIAL(self):
        pane = self.Pane('remotedb')
        data = Data.Inst()
        pane.ColoursSet('MODAL_BASE', 'MODAL_BRIGHT', 'MODAL_HIGHLIGHT')
        pane.ResetFields()
        
        pane.AddWrappedTextField(Lang("Please enter the configuration details"))
        pane.NewLine()
        
        pane.AddInputField(Lang("Initiator IQN",  26), data.remotedb.defaultlocaliqn(''), 'localiqn')
        pane.AddInputField(Lang("Port number",  26), '3260', 'port')
        pane.AddInputField(Lang("Hostname of iSCSI target",  26), '', 'remotehost')
        pane.AddInputField(Lang("Username",  26), data.remotedb.username(''), 'username')
        pane.AddPasswordField(Lang("Password",  26), data.remotedb.password(''), 'password')
                
        pane.AddKeyHelpField( {
            Lang("<Esc>") : Lang("Cancel"),
            Lang("<Enter>") : Lang("Next/OK"),
            Lang("<Tab>") : Lang("Next")
        } )

        if pane.CurrentInput() is None:
            pane.InputIndexSet(0)
            
    def UpdateFieldsCHOOSEIQN(self):
        pane = self.Pane('remotedb')
        pane.ColoursSet('MODAL_BASE', 'MODAL_BRIGHT', 'MODAL_MENU_HIGHLIGHT')
        pane.ResetFields()
        
        pane.AddTitleField(Lang("Please select from the list of discovered IQNs"))
        pane.AddMenuField(self.iqnMenu)
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )

    def UpdateFieldsCHOOSELUN(self):
        pane = self.Pane('remotedb')
        pane.ColoursSet('MODAL_BASE', 'MODAL_BRIGHT', 'MODAL_MENU_HIGHLIGHT')
        pane.ResetFields()
        
        pane.AddTitleField(Lang("Please select a LUN from the chosen IQN"))
        pane.AddMenuField(self.lunMenu)
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
            
    def UpdateFieldsCREATEDB(self):
        pane = self.Pane('remotedb')
        pane.ColoursSet('MODAL_BASE', 'MODAL_BRIGHT', 'MODAL_HIGHLIGHT')
        pane.ResetFields()
        
        if self.dbPresent or self.dbPresent is None: # Database is present but the user has chosen not to use it
            pane.AddWrappedBoldTextField(Lang("Please confirm that you would like to format the following disk.  Data currently on this disk cannot be recovered after this step."))
        else:
            pane.AddWrappedBoldTextField(Lang("No database can be found on the remote disk.  Would you like to format it and prepare a new database?  Data currently on this disk cannot be recovered after this step."))
        pane.NewLine()
        pane.AddWrappedBoldTextField(Lang("Remote iSCSI disk"))
        pane.AddWrappedTextField(self.IQNString(self.chosenIQN, self.chosenLUN))

        pane.AddKeyHelpField( { Lang("<F8>") : Lang("Format and Create"), Lang("<Esc>") : Lang("Cancel") } )

    def UpdateFieldsUSEDB(self):
        pane = self.Pane('remotedb')
        pane.ColoursSet('MODAL_BASE', 'MODAL_BRIGHT', 'MODAL_MENU_HIGHLIGHT')
        pane.ResetFields()
        
        if self.dbPresent is None: # i.e. we don't know
            pane.AddWrappedBoldTextField(Lang("Would you like to use a database already on the disk, or format it and create a new database?"))
        else:
            pane.AddWrappedBoldTextField(Lang("A database is already present on the remote disk.  Please select an option."))
        pane.NewLine()
        pane.AddWrappedBoldTextField(Lang("Remote iSCSI disk"))
        pane.AddWrappedTextField(self.IQNString(self.chosenIQN, self.chosenLUN))
        pane.NewLine()
        pane.AddMenuField(self.useMenu)
        
        pane.AddKeyHelpField( { Lang("<Up/Down>") : Lang("Select"), Lang("<Enter>") : Lang("OK") } )

    def UpdateFields(self):
        self.Pane('remotedb').ResetPosition()
        getattr(self, 'UpdateFields'+self.state)() # Despatch method named 'UpdateFields'+self.state
        
    def HandleKeyINITIAL(self, inKey):
        handled = True
        pane = self.Pane('remotedb')

        if inKey == 'KEY_ENTER':
            if not pane.IsLastInput():
                pane.ActivateNextInput()
            else:
                self.newConf = pane.GetFieldValues()
                try:
                    self.layout.TransientBanner(Lang("Probing for IQNs..."))
                    self.probedIQNs = RemoteDB.Inst().ProbeIQNs(self.newConf)
                    self.ChangeState('CHOOSEIQN')
                except Exception, e:
                    self.layout.PushDialogue(InfoDialogue(self.layout, self.parent, Lang("Failed: ")+Lang(e)))
                    
        elif inKey == 'KEY_TAB':
            pane.ActivateNextInput()
        elif inKey == 'KEY_BTAB':
            pane.ActivatePreviousInput()
        elif pane.CurrentInput().HandleKey(inKey):
            pass # Leave handled as True
        else:
            handled = False
        return handled

    def HandleKeyCHOOSEIQN(self, inKey):
        return self.iqnMenu.HandleKey(inKey)

    def HandleKeyCHOOSELUN(self, inKey):
        return self.lunMenu.HandleKey(inKey)
    
    def HandleKeyUSEDB(self, inKey):
        return self.useMenu.HandleKey(inKey)
        
    def HandleKeyCREATEDB(self, inKey):
        handled = False
        
        if inKey == 'KEY_F(8)':
            self.layout.TransientBanner(Lang("Formatting..."))
            Data.Inst().StopXAPI()
            try:
                try:
                    self.dbPresent = RemoteDB.Inst().FormatLUN(self.newConf, self.chosenIQN, self.chosenLUN)
                    self.layout.PopDialogue()
                    self.layout.PushDialogue(InfoDialogue(self.layout, self.parent,
                        Lang("Format, Creation, and Configuration Successful")))
                except Exception, e:
                    self.layout.PushDialogue(InfoDialogue(self.layout, self.parent, Lang("Failed: ")+Lang(e)))
            finally:
                Data.Inst().StartXAPI()
                Data.Inst().Update()
            handled = True
            
        return handled
    
    def HandleKey(self, inKey):
        handled = False
        if hasattr(self, 'HandleKey'+self.state):
            handled = getattr(self, 'HandleKey'+self.state)(inKey)
        
        if not handled and inKey == 'KEY_ESCAPE':
            self.layout.PopDialogue()
            handled = True

        return handled
        
    def HandleIQNChoice(self, inChoice):
        if inChoice is None:
            self.ChangeState('CUSTOMIQN')
        else:
            self.layout.TransientBanner(Lang("Probing for LUNs..."))
            self.chosenIQN = self.probedIQNs[inChoice]
            self.probedLUNs = RemoteDB.Inst().ProbeLUNs(self.newConf, self.chosenIQN)
            
            self.ChangeState('CHOOSELUN')

    def HandleLUNChoice(self, inChoice):
        if inChoice is None:
            self.ChangeState('CUSTOMLUN')
        else:
            self.layout.TransientBanner(Lang("Scanning target LUN..."))
            
            self.chosenLUN = self.probedLUNs[inChoice]

            self.dbPresent = RemoteDB.Inst().TestLUN(self.newConf, self.chosenIQN, self.chosenLUN)
            
            if self.dbPresent or self.dbPresent is None:
                self.ChangeState('USEDB')
            else:
                self.ChangeState('CREATEDB')

    def HandleUseChoice(self, inChoice):
        if inChoice == 'USE':
            self.layout.TransientBanner(Lang("Configuring Remote Database..."))
            Data.Inst().StopXAPI()
            try:
                try:
                    self.dbPresent = RemoteDB.Inst().ReadyForUse(self.newConf, self.chosenIQN, self.chosenLUN)
                    self.layout.PopDialogue()
                    self.layout.PushDialogue(InfoDialogue(self.layout, self.parent,
                        Lang("Configuration Successful")))
                except Exception, e:
                    self.layout.PushDialogue(InfoDialogue(self.layout, self.parent, Lang("Failed: ")+Lang(e)))
            finally:
                Data.Inst().StartXAPI()
                Data.Inst().Update()
        elif inChoice == 'FORMAT':
            self.ChangeState('CREATEDB')
        else:
            self.PopDialogue()

class RemoteShellDialogue(Dialogue):
    def __init__(self, inLayout, inParent):
        Dialogue.__init__(self, inLayout, inParent)

        paneHeight = 9
        pane = self.NewPane('remoteshell', DialoguePane(3, 12 - paneHeight/2, 74, paneHeight, self.parent))
        pane.Win().TitleSet(Lang("Configure Remote Shell"))
        pane.AddBox()

        self.remoteShellMenu = Menu(self, None, Lang("Configure Remote Shell"), [
            ChoiceDef(Lang("Enable"), lambda: self.HandleChoice(True) ), 
            ChoiceDef(Lang("Disable"), lambda: self.HandleChoice(False) )
            ])
    
        self.UpdateFields()
        
    def UpdateFields(self):
        pane = self.Pane('remoteshell')
        pane.ColoursSet('MODAL_BASE', 'MODAL_BRIGHT', 'MODAL_MENU_HIGHLIGHT')
        pane.ResetFields()
        
        pane.AddTitleField(Lang("Please select an option"))
        pane.AddMenuField(self.remoteShellMenu)
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )

    def HandleKey(self, inKey):
        handled = self.remoteShellMenu.HandleKey(inKey)
        
        if not handled and inKey == 'KEY_ESCAPE':
            self.layout.PopDialogue()
            handled = True

        return handled
                
    def HandleChoice(self,  inChoice):
        data = Data.Inst()
        self.layout.PopDialogue()
        
        try:
            data.ConfigureRemoteShell(inChoice)
        except Exception, e:
            self.layout.PushDialogue(InfoDialogue(self.layout, self.parent, Lang("Failed: ")+Lang(e)))
        else:
            self.layout.PushDialogue(BannerDialogue(self.layout, self.parent, Lang("Configuration Updated.  Resetting the sshd process...")))
            self.layout.Refresh()
            self.layout.DoUpdate()
            time.sleep(2)
            if inChoice:
                self.layout.SubshellCommandSet('/etc/init.d/sshd start && sleep 2')
            else:
                self.layout.SubshellCommandSet('/etc/init.d/sshd stop && sleep 2')

class VerboseBootDialogue(Dialogue):
    def __init__(self, inLayout, inParent):
        Dialogue.__init__(self, inLayout, inParent)

        paneHeight = 9
        pane = self.NewPane('verboseboot', DialoguePane(3, 12 - paneHeight/2, 74, paneHeight, self.parent))
        pane.Win().TitleSet(Lang("Configure Verbose Boot Mode"))
        pane.AddBox()

        self.remoteShellMenu = Menu(self, None, Lang("Configure Verbose Boot Mode"), [
            ChoiceDef(Lang("Enable"), lambda: self.HandleChoice(True) ), 
            ChoiceDef(Lang("Disable"), lambda: self.HandleChoice(False) )
            ])
    
        self.UpdateFields()
        
    def UpdateFields(self):
        pane = self.Pane('verboseboot')
        pane.ColoursSet('MODAL_BASE', 'MODAL_BRIGHT', 'MODAL_MENU_HIGHLIGHT')
        pane.ResetFields()
        
        pane.AddTitleField(Lang("Please select an option"))
        pane.AddMenuField(self.remoteShellMenu)
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )

    def HandleKey(self, inKey):
        handled = self.remoteShellMenu.HandleKey(inKey)
        
        if not handled and inKey == 'KEY_ESCAPE':
            self.layout.PopDialogue()
            handled = True

        return handled
                
    def HandleChoice(self, inChoice):
        data = Data.Inst()
        self.layout.PopDialogue()
        self.layout.TransientBanner(Lang("Updating..."))
        
        try:
            data.SetVerboseBoot(inChoice)
        except Exception, e:
            self.layout.PushDialogue(InfoDialogue(self.layout, self.parent, Lang("Failed: ")+Lang(e)))
        else:
            self.layout.PushDialogue(InfoDialogue(self.layout, self.parent, Lang("Configuration Updated")))

class ValidateDialogue(Dialogue):
    def __init__(self, inLayout, inParent):
        Dialogue.__init__(self, inLayout, inParent)

        data = Data.Inst()

        paneHeight = 10
        pane = self.NewPane('validate', DialoguePane(3, 12 - paneHeight/2, 74, paneHeight, self.parent))
        
        pane.ColoursSet('MODAL_BASE', 'MODAL_BRIGHT', 'MODAL_HIGHLIGHT')
        pane.Win().TitleSet(Lang("Validate Server Configuration"))
        pane.AddBox()
    
        if 'vmx' in data.cpuinfo.flags([]) or 'svm' in data.cpuinfo.flags([]):
            self.vtResult = Lang("OK")
        else:
            self.vtResult = Lang("Not OK")
        
        # If there is an SR that allows vdi_create, signal SR OK
        self.srResult = "Not Present"
        for pbd in data.host.PBDs([]):
            sr = pbd.get('SR', {})
            if 'vdi_create' in sr['allowed_operations']:
                self.srResult = 'OK'
        
        self.netResult = "Not OK"
        if len(data.derived.managementpifs([])) > 0:
            managementPIF = data.derived.managementpifs()[0]
            if managementPIF['currently_attached']:
                self.netResult = "OK"
            else:
                self.netResult = "Not connected"

        self.UpdateFields()
        
    def UpdateFields(self):
        pane = self.Pane('validate')
        pane.ResetFields()
        
        pane.AddTitleField(Lang("Validation Results"))
        pane.AddStatusField(Lang("VT enabled on CPU", 50), self.vtResult)
        pane.AddStatusField(Lang("Local default storage repository", 50), self.srResult)
        pane.AddStatusField(Lang("Management network interface", 50), self.netResult)
        
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK") } )

    def HandleKey(self, inKey):
        handled = False
        if inKey == 'KEY_ENTER' or inKey == 'KEY_ESCAPE':
            self.layout.PopDialogue()
            handled = True

        return handled

class FileDialogue(Dialogue):
    def __init__(self, inLayout, inParent):
        Dialogue.__init__(self, inLayout, inParent)

        self.vdiMount = None
        self.ChangeState('INITIAL')
    
    def Custom(self, inKey):
        return self.custom.get(inKey, None)
    
    def BuildPaneBase(self, inHeight):
        paneHeight = min(inHeight,  22)
        pane = self.NewPane('file', DialoguePane(3, 12 - paneHeight/2, 74, paneHeight, self.parent))
        pane.Win().TitleSet(self.Custom('title'))
        pane.AddBox()
    
    def BuildPaneINITIAL(self):
        if self.Custom('mode') == 'rw':
            self.deviceList = FileUtils.DeviceList(True) # Writable devices only
        else:
            self.deviceList = FileUtils.DeviceList(False) # Writable and read-only devices
        
        choiceDefs = []
        for device in self.deviceList:
            choiceDefs.append(ChoiceDef(device.name, lambda: self.HandleDeviceChoice(self.deviceMenu.ChoiceIndex()) ) )

        if len(choiceDefs) == 0:
            choiceDefs.append(ChoiceDef('<No devices available>', lambda: None)) # Avoid empty menu

        self.deviceMenu = Menu(self, None, Lang("Select Device"), choiceDefs)

        self.BuildPaneBase(7+len(choiceDefs))
        self.UpdateFields()
    
    def BuildPaneUSBNOTFORMATTED(self):
        self.BuildPaneBase(6)
        self.UpdateFields()
        
    def BuildPaneUSBNOTMOUNTABLE(self):
        self.BuildPaneBase(8)
        self.UpdateFields()
    
    def BuildPaneFILES(self):
        self.BuildPaneBase(7+min(len(self.fileList)+1, 10)) # Menu field limited to 10 lines, +1 is for custom filename field
        
        choiceDefs = []
        for filename in self.fileList:
            displayName = "%-60.60s%10.10s" % (filename, self.vdiMount.SizeString(filename))
            choiceDefs.append(ChoiceDef(displayName, lambda: self.HandleFileChoice(self.fileMenu.ChoiceIndex()) ) )

        choiceDefs.append(ChoiceDef(Lang('Enter Custom Filename'), lambda: self.HandleFileChoice(None)))
        self.fileMenu = Menu(self, None, Lang("Select File"), choiceDefs)
        self.UpdateFields()
        
    def BuildPaneCONFIRM(self):
        self.BuildPaneBase(12)
        self.UpdateFields()

    def BuildPaneCUSTOM(self):
        self.BuildPaneBase(10)
        self.UpdateFields()
    
    def ChangeState(self, inState):
        self.state = inState
        getattr(self, 'BuildPane'+self.state)() # Despatch method named 'BuildPane'+self.state
    
    def UpdateFields(self):
        self.Pane('file').ResetPosition()
        getattr(self, 'UpdateFields'+self.state)() # Despatch method named 'UpdateFields'+self.state
        
    def UpdateFieldsINITIAL(self):
        pane = self.Pane('file')
        pane.ColoursSet('MODAL_BASE', 'MODAL_BRIGHT', 'MODAL_MENU_HIGHLIGHT')
        pane.ResetFields()
        
        pane.AddTitleField(self.Custom('deviceprompt'))
        pane.AddMenuField(self.deviceMenu)
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel"), 
            "<F5>" : Lang("Rescan") } )

    def UpdateFieldsUSBNOTFORMATTED(self):
        pane = self.Pane('file')
        pane.ColoursSet('MODAL_BASE', 'MODAL_BRIGHT', 'MODAL_MENU_HIGHLIGHT')
        pane.ResetFields()
        
        pane.AddWrappedBoldTextField(Lang("This USB media is not formatted.  Would you like to format it now?"))
        pane.AddKeyHelpField( { Lang("<F8>") : Lang("Format media"), Lang("<Esc>") : Lang("Exit") } )

    def UpdateFieldsUSBNOTMOUNTABLE(self):
        pane = self.Pane('file')
        pane.ColoursSet('MODAL_BASE', 'MODAL_BRIGHT', 'MODAL_MENU_HIGHLIGHT')
        pane.ResetFields()
        
        pane.AddWrappedBoldTextField(Lang("This USB media contains data but this application cannot mount it.  Would you like to format the media?  This will erase all data on the media."))
        pane.AddKeyHelpField( { Lang("<F8>") : Lang("Format Media"), Lang("<Esc>") : Lang("Exit") } )

    def UpdateFieldsFILES(self):
        pane = self.Pane('file')
        pane.ColoursSet('MODAL_BASE', 'MODAL_BRIGHT', 'MODAL_MENU_HIGHLIGHT')
        pane.ResetFields()
        
        pane.AddTitleField(self.Custom('fileprompt'))
        pane.AddMenuField(self.fileMenu)
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )

    def UpdateFieldsCUSTOM(self):
        pane = self.Pane('file')
        pane.ColoursSet('MODAL_BASE', 'MODAL_BRIGHT', 'MODAL_HIGHLIGHT')
        pane.ResetFields()
        
        pane.AddTitleField(Lang("Enter Filename"))
        pane.AddInputField(Lang("Filename",  16), FirstValue(self.Custom('filename'), ''), 'filename')
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Exit") } )
        if pane.CurrentInput() is None:
            pane.InputIndexSet(0)

    def UpdateFieldsCONFIRM(self):
        pane = self.Pane('file')
        pane.ColoursSet('MODAL_BASE', 'MODAL_BRIGHT', 'MODAL_HIGHLIGHT')
        pane.ResetFields()
        
        pane.AddTitleField(self.Custom('confirmprompt'))
        pane.AddWrappedBoldTextField(Lang("Device"))
        pane.AddWrappedTextField(self.deviceName)
        pane.NewLine()
        
        if self.Custom('mode') == 'rw':
            fileSize = ' ('+self.vdiMount.SizeString(self.filename, Lang('New file'))+')'
        else:
            fileSize = ' ('+self.vdiMount.SizeString(self.filename, Lang('File not found'))+')'
        
        pane.AddWrappedBoldTextField(Lang("File"))
        pane.AddWrappedTextField(self.filename+fileSize)
        
        pane.AddKeyHelpField( { Lang("<F8>") : Lang("OK"), Lang("<Esc>") : Lang("Exit") } )

    def HandleKey(self, inKey):
        handled = False
        if hasattr(self, 'HandleKey'+self.state):
            handled = getattr(self, 'HandleKey'+self.state)(inKey)
        
        if not handled and inKey == 'KEY_ESCAPE':
            self.layout.PopDialogue()
            self.PreExitActions()
            handled = True

        return handled
        
    def HandleKeyINITIAL(self, inKey):
        handled = self.deviceMenu.HandleKey(inKey)
        
        if not handled and inKey == 'KEY_F(5)':
            self.layout.PushDialogue(BannerDialogue(self.layout, self.parent, Lang("Rescanning...")))
            self.layout.Refresh()
            self.layout.DoUpdate()
            self.layout.PopDialogue()
            self.BuildPaneINITIAL() # Updates self.deviceList
            time.sleep(0.5) # Display rescanning box for a reasonable time
            self.layout.Refresh()
            handled = True
            
        return handled
    
    def HandleKeyUSBNOTFORMATTED(self, inKey):
        handled = False
        if inKey == 'KEY_F(8)':
            self.layout.PushDialogue(BannerDialogue(self.layout, self.parent, Lang("Formatting...")))
            self.layout.Refresh()
            self.layout.DoUpdate()
            self.layout.PopDialogue()

            try:
                FileUtils.USBFormat(self.vdi)
                self.HandleDevice()
            except Exception, e:
                self.layout.PushDialogue(InfoDialogue(self.layout, self.parent, Lang("Formatting Failed"), Lang(e)))

            handled = True

        return handled
    
    def HandleKeyUSBNOTMOUNTABLE(self, inKey):
        return self.HandleKeyUSBNOTFORMATTED(inKey)
    
    def HandleKeyFILES(self, inKey):
        return self.fileMenu.HandleKey(inKey)
        
    def HandleKeyCUSTOM(self, inKey):
        handled = True
        pane = self.Pane('file')
        if pane.CurrentInput() is None:
            pane.InputIndexSet(0)
        if inKey == 'KEY_ENTER':
            inputValues = pane.GetFieldValues()
            self.filename = inputValues['filename']
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
    
    def HandleDeviceChoice(self, inChoice):
        self.deviceName = self.deviceList[inChoice].name
        self.vdi = self.deviceList[inChoice].vdi
        self.HandleDevice()
        
    def HandleDevice(self):
        try:

            self.vdiMount = None

            self.layout.PushDialogue(BannerDialogue(self.layout, self.parent, Lang("Mounting device...")))
            self.layout.Refresh()
            self.layout.DoUpdate()

            self.vdiMount = MountVDI(self.vdi, self.Custom('mode'))

            
            self.layout.PopDialogue()
            self.layout.PushDialogue(BannerDialogue(self.layout, self.parent, Lang("Scanning device...")))
            self.layout.Refresh()
            self.layout.DoUpdate()
            
            self.fileList = self.vdiMount.Scan(self.Custom('searchregexp'), 500) # Limit number of files to avoid colossal menu
            
            self.layout.PopDialogue()
            
            self.ChangeState('FILES')
        
        except USBNotFormatted:
            self.layout.PopDialogue()
            self.ChangeState('USBNOTFORMATTED')
        except USBNotMountable:
            self.layout.PopDialogue()
            self.ChangeState('USBNOTMOUNTABLE')
        except Exception, e:
            try:
                self.PreExitActions()
            except Exception:
                pass # Ignore failue
            self.layout.PopDialogue()
            self.layout.PushDialogue(InfoDialogue(self.layout, self.parent, Lang("Operation Failed"), Lang(e)))

    def HandleFileChoice(self, inChoice):
        if inChoice is None:
            self.ChangeState('CUSTOM')
        else:
            self.filename = self.fileList[inChoice]
            self.ChangeState('CONFIRM')
    
    def PreExitActions(self):
        if self.vdiMount is not None:
            self.vdiMount.Unmount()
            self.vdiMount = None

class PatchDialogue(FileDialogue):
    def __init__(self, inLayout, inParent):

        self.custom = {
            'title' : Lang("Apply Software Upgrade Or Patch"),
            'searchregexp' : r'.*\.xbk$',  # Type of backup file is .xbk
            'deviceprompt' : Lang("Select The Device Containing The Patch"), 
            'fileprompt' : Lang("Select The Patch File"),
            'confirmprompt' : Lang("Press <F8> To Begin The Update/Patch Process"),
            'mode' : 'ro'
        }
        FileDialogue.__init__(self, inLayout, inParent) # Must fill in self.custom before calling __init__
        
    def DoAction(self):
        success = False
        
        self.layout.PopDialogue()
        
        self.layout.PushDialogue(BannerDialogue(self.layout, self.parent,
            Lang("Applying patch... This make take several minutes.  Press <Ctrl-C> to abort.")))
            
        try:
            try:
                self.layout.Refresh()
                self.layout.DoUpdate()
                
                hostRef = Data.Inst().host.uuid(None)
                if hostRef is None:
                    raise Exception("Internal error 1")
                    
                filename = self.vdiMount.MountedPath(self.filename)
                FileUtils.AssertSafePath(filename)
                command = "/opt/xensource/bin/xe update-upload file-name='"+filename+"' host-uuid="+hostRef
                status, output = commands.getstatusoutput(command)
                
                if status != 0:
                    raise Exception(output)
                
                self.layout.PopDialogue()
                self.layout.PushDialogue(InfoDialogue(self.layout, self.parent,
                    Lang("Patch Successful"), Lang("Please reboot to use the newly installed software.")))

            except Exception, e:
                self.layout.PopDialogue()
                self.layout.PushDialogue(InfoDialogue(self.layout, self.parent, Lang("Software Upgrade or Patch Failed"), Lang(e)))
                
        finally:
            try:
                self.PreExitActions()
            except Exception, e:
                self.layout.PushDialogue(InfoDialogue(self.layout, self.parent, Lang("Software Upgrade or Patch Failed"), Lang(e)))

class BackupDialogue(FileDialogue):
    def __init__(self, inLayout, inParent):

        self.custom = {
            'title' : Lang("Backup Server State"),
            'searchregexp' : r'.*\.xbk$',  # Type of backup file is .xbk
            'deviceprompt' : Lang("Select The Device To Save To"), 
            'fileprompt' : Lang("Choose The Backup Filename"),
            'filename' : 'backup.xbk',
            'confirmprompt' : Lang("Press <F8> To Begin The Backup Process"),
            'mode' : 'rw'
        }
        FileDialogue.__init__(self, inLayout, inParent) # Must fill in self.custom before calling __init__
        
    def DoAction(self):
        filename = self.vdiMount.MountedPath(self.filename)
        if os.path.isfile(filename):
            self.layout.PushDialogue(QuestionDialogue(self.layout,  self.parent,
                Lang("File already exists.  Do you want to overwrite it?"), lambda x: self.DoOverwriteChoice(x)))
        else:
            self.DoCommit()
    
    def DoOverwriteChoice(self, inChoice):
        if inChoice == 'y':
            filename = self.vdiMount.MountedPath(self.filename)
            os.remove(filename)
            self.DoCommit()
        else:
            self.ChangeState('FILES')
    
    def DoCommit(self):
        success = False
        
        self.layout.PopDialogue()
        
        self.layout.PushDialogue(BannerDialogue(self.layout, self.parent,
            Lang("Saving to backup... This make take several minutes.  Press <Ctrl-C> to abort.")))
            
        try:
            try:
                self.layout.Refresh()
                self.layout.DoUpdate()
                
                hostRef = Data.Inst().host.uuid(None)
                if hostRef is None:
                    raise Exception("Internal error 1")
                    
                filename = self.vdiMount.MountedPath(self.filename)
                FileUtils.AssertSafePath(filename)
                command = "/opt/xensource/bin/xe host-backup file-name='"+filename+"' host="+hostRef
                status, output = commands.getstatusoutput(command)
                
                if status != 0:
                    raise Exception(output)
                
                self.layout.PopDialogue()
                self.layout.PushDialogue(InfoDialogue(self.layout, self.parent,
                    Lang("Backup Successful")))

            except Exception, e:
                self.layout.PopDialogue()
                self.layout.PushDialogue(InfoDialogue(self.layout, self.parent, Lang("Backup Failed"), Lang(e)))
                
        finally:
            try:
                self.PreExitActions()
            except Exception, e:
                self.layout.PushDialogue(InfoDialogue(self.layout, self.parent, Lang("Backup Failed"), Lang(e)))

class RestoreDialogue(FileDialogue):
    def __init__(self, inLayout, inParent):

        self.custom = {
            'title' : Lang("Restore Server State"),
            'searchregexp' : r'.*\.xbk$',  # Type of backup file is .xbk
            'deviceprompt' : Lang("Select The Device Containing The Backup File"), 
            'fileprompt' : Lang("Select The Backup File"),
            'confirmprompt' : Lang("Press <F8> To Begin The Restore Process"),
            'mode' : 'ro'
        }
        FileDialogue.__init__(self, inLayout, inParent) # Must fill in self.custom before calling __init__
        
    def DoAction(self):
        success = False
        
        self.layout.PopDialogue()
        
        self.layout.PushDialogue(BannerDialogue(self.layout, self.parent,
            Lang("Restoring from backup... This may take several minutes.")))
            
        try:
            try:
                self.layout.Refresh()
                self.layout.DoUpdate()
                
                hostRef = Data.Inst().host.uuid(None)
                if hostRef is None:
                    raise Exception("Internal error 1")
                    
                filename = self.vdiMount.MountedPath(self.filename)
                FileUtils.AssertSafePath(filename)
                command = "/opt/xensource/bin/xe host-restore file-name='"+filename+"' host="+hostRef
                status, output = commands.getstatusoutput(command)
                
                if status != 0:
                    raise Exception(output)
                
                self.layout.PopDialogue()
                self.layout.PushDialogue(InfoDialogue(self.layout, self.parent,
                    Lang("Restore Successful"), Lang("Please reboot to use the new backup.")))

            except Exception, e:
                self.layout.PopDialogue()
                self.layout.PushDialogue(InfoDialogue(self.layout, self.parent, Lang("Restore Failed"), Lang(e)))
                
        finally:
            try:
                self.PreExitActions()
            except Exception, e:
                self.layout.PushDialogue(InfoDialogue(self.layout, self.parent, Lang("Restore Failed"), Lang(e)))

class LicenceDialogue(FileDialogue):
    def __init__(self, inLayout, inParent):

        self.custom = {
            'title' : Lang("Install License"),
            'searchregexp' : r'.*licen[cs]e',  # Licence files always contain the string licence or license
            'deviceprompt' : Lang("Select The Device Containing The License File"), 
            'fileprompt' : Lang("Select The License File"),
            'confirmprompt' : Lang("Press <F8> To Install The License"),
            'mode' : 'ro'
        }
        FileDialogue.__init__(self, inLayout, inParent) # Must fill in self.custom before calling __init__
        
    def DoAction(self):
        success = False
        
        self.layout.PopDialogue()
        
        self.layout.PushDialogue(BannerDialogue(self.layout, self.parent,
            Lang("Installing License...")))
            
        try:
            try:
                self.layout.Refresh()
                self.layout.DoUpdate()
                
                hostRef = Data.Inst().host.uuid(None)
                if hostRef is None:
                    raise Exception("Internal error 1")
                    
                filename = self.vdiMount.MountedPath(self.filename)
                FileUtils.AssertSafePath(filename)
                command = "/opt/xensource/bin/xe host-license-add license-file='"+filename+"' host-uuid="+hostRef
                status, output = commands.getstatusoutput(command)
                
                if status != 0:
                    raise Exception(output)
                
                Data.Inst().Update()
                self.layout.PopDialogue()
                self.layout.PushDialogue(InfoDialogue(self.layout, self.parent,
                    Lang("License Installed Successfully")))

            except Exception, e:
                self.layout.PopDialogue()
                self.layout.PushDialogue(InfoDialogue(self.layout, self.parent, Lang("License Installation Failed"), Lang(e)))
                
        finally:
            try:
                self.PreExitActions()
            except Exception, e:
                self.layout.PushDialogue(InfoDialogue(self.layout, self.parent, Lang("License Installation Failed"), Lang(e)))

class SaveBugReportDialogue(FileDialogue):
    def __init__(self, inLayout, inParent):

        self.custom = {
            'title' : Lang("Save Bug Report"),
            'searchregexp' : r'.*',  # Type of bugtool file is .tar
            'deviceprompt' : Lang("Select The Destination Device"), 
            'fileprompt' : Lang("Choose A Destination Filename"),
            'filename' : 'bugreport.tar',
            'confirmprompt' : Lang("Press <F8> To Save The Bug Report"),
            'mode' : 'rw'
        }
        FileDialogue.__init__(self, inLayout, inParent) # Must fill in self.custom before calling __init__
        
    def DoAction(self):
        success = False
        
        self.layout.PopDialogue()
        
        self.layout.PushDialogue(BannerDialogue(self.layout, self.parent,
            Lang("Saving Bug Report...")))
            
        try:
            try:
                self.layout.Refresh()
                self.layout.DoUpdate()

                filename = self.vdiMount.MountedPath(self.filename)
                FileUtils.AssertSafePath(filename)

                file = open(filename, "w")
                # xen-bugtool requires a value for $USER
                command = "( export USER=root && /usr/sbin/xen-bugtool --yestoall --silent --output=tar --outfd="+str(file.fileno()) + ' )'
                status, output = commands.getstatusoutput(command)
                file.close()

                if status != 0:
                    raise Exception(output)

                self.layout.PopDialogue()
                self.layout.PushDialogue(InfoDialogue(self.layout, self.parent,
                    Lang("Saved Bug Report")))

            except Exception, e:
                self.layout.PopDialogue()
                self.layout.PushDialogue(InfoDialogue(self.layout, self.parent, Lang("Save Failed"), Lang(e)))
                
        finally:
            try:
                self.PreExitActions()
            except Exception, e:
                self.layout.PushDialogue(InfoDialogue(self.layout, self.parent, Lang("Save Failed"), Lang(e)))

class TestNetworkDialogue(Dialogue):
    def __init__(self, inLayout, inParent):
        Dialogue.__init__(self, inLayout, inParent)

        paneHeight = 11
        paneHeight = min(paneHeight,  22)
        pane = self.NewPane('testnetwork', DialoguePane(3, 12 - paneHeight/2, 74, paneHeight, self.parent))
        pane.Win().TitleSet(Lang("Test Network Configuration"))
        pane.AddBox()
        
        gatewayName = Data.Inst().ManagementGateway()
        if gatewayName is None: gatewayName = 'Unknown'
        
        self.testMenu = Menu(self, None, Lang("Select Test Type"), [
            ChoiceDef(Lang("Ping local address 127.0.0.1"), lambda: self.HandleTestChoice('local') ), 
            ChoiceDef(Lang("Ping gateway address")+" ("+gatewayName+")", lambda: self.HandleTestChoice('gateway') ), 
            ChoiceDef(Lang("Ping citrixxenserver.com"), lambda: self.HandleTestChoice('xenserver') ), 
            ChoiceDef(Lang("Ping custom address"), lambda: self.HandleTestChoice('custom') ), 
            ])
    
        self.customIP = '0.0.0.0'
        self.state = 'INITIAL'
    
        self.UpdateFields()

    def UpdateFields(self):
        self.Pane('testnetwork').ResetPosition()
        getattr(self, 'UpdateFields'+self.state)() # Despatch method named 'UpdateFields'+self.state
        
    def UpdateFieldsINITIAL(self):
        pane = self.Pane('testnetwork')
        pane.ColoursSet('MODAL_BASE', 'MODAL_BRIGHT', 'MODAL_MENU_HIGHLIGHT')
        pane.ResetFields()
        
        pane.AddTitleField(Lang("Select Test"))
        pane.AddMenuField(self.testMenu)
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
        
    def UpdateFieldsCUSTOM(self):
        pane = self.Pane('testnetwork')
        pane.ColoursSet('MODAL_BASE', 'MODAL_BRIGHT', 'MODAL_HIGHLIGHT')
        pane.ResetFields()
        
        pane.AddTitleField(Lang("Enter hostname or IP address to ping"))
        pane.AddInputField(Lang("Address",  16), self.customIP, 'address')
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Exit") } )
        if pane.CurrentInput() is None:
            pane.InputIndexSet(0)
            
    def HandleKey(self, inKey):
        handled = False
        if hasattr(self, 'HandleKey'+self.state):
            handled = getattr(self, 'HandleKey'+self.state)(inKey)
        
        if not handled and inKey == 'KEY_ESCAPE':
            self.layout.PopDialogue()
            handled = True

        return handled
        
    def HandleKeyINITIAL(self, inKey):
        handled = self.testMenu.HandleKey(inKey)
        if not handled and inKey == 'KEY_LEFT':
            self.layout.PopDialogue()
            handled = True
        return handled
        
    def HandleKeyCUSTOM(self, inKey):
        handled = True
        pane = self.Pane('testnetwork')
        if pane.CurrentInput() is None:
            pane.InputIndexSet(0)
        if inKey == 'KEY_ENTER':
            inputValues = pane.GetFieldValues()
            self.customIP = inputValues['address']
            self.DoPing(self.customIP)
            self.state = 'INITIAL'
            
        elif pane.CurrentInput().HandleKey(inKey):
            pass # Leave handled as True
        else:
            handled = False
        return handled
        
    def HandleTestChoice(self,  inChoice):
        pingTarget = None
        custom = False
        if inChoice == 'local':
            pingTarget = '127.0.0.1'
        elif inChoice == 'gateway':
            pingTarget = Data.Inst().ManagementGateway()
        elif inChoice == 'xenserver':
            pingTarget = 'citrixxenserver.com'
        else:
            custom = True

        if custom:
            self.state = 'CUSTOM'
            self.UpdateFields()
            self.Pane('testnetwork').InputIndexSet(0)
        else:
            self.DoPing(pingTarget)

    def DoPing(self, inAddress):
        success = False
        output = 'Cannot determine address to ping'
            
        if inAddress is not None:
            try:
                (success,  output) = Data.Inst().Ping(inAddress)
            except Exception,  e:
                output = Lang(e)
            
        if success:
            self.layout.PushDialogue(InfoDialogue(self.layout, self.parent, Lang("Ping successful"), output))
        else:
            self.layout.PushDialogue(InfoDialogue(self.layout, self.parent, Lang("Ping failed"), output))
        
