# Copyright (c) Citrix Systems 2007. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

from XSConsoleStandard import *
        
class ChangePasswordDialogue(Dialogue):
    def __init__(self, inLayout, inParent,  inText = None,  inSuccessFunc = None):
        Dialogue.__init__(self, inLayout, inParent)
        self.text = inText
        self.successFunc = inSuccessFunc
        self.isPasswordSet = Auth.Inst().IsPasswordSet()

        pane = self.NewPane(DialoguePane(self.parent))
        pane.TitleSet("Change Password")
        pane.AddBox()
        self.UpdateFields()
        
    def UpdateFields(self):
        pane = self.Pane()
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
        
        if pane.InputIndex() is None:
            pane.InputIndexSet(0) # Activate first field for input
        
    def HandleKey(self, inKey):
        handled = True
        pane = self.Pane()
        if inKey == 'KEY_ESCAPE':
            Layout.Inst().PopDialogue()
        elif inKey == 'KEY_ENTER':
            if not pane.IsLastInput():
                pane.ActivateNextInput()
            else:
                inputValues = pane.GetFieldValues()

                Layout.Inst().TransientBanner(Lang("Changing password..."))
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
                    if self.isPasswordSet:
                        # Only remove the dialogue if this isn't the initial password set (which needs to succeed)
                        Layout.Inst().PopDialogue()
                    else:
                        # Disable the input field so that it gets reactivated by UpdateFields  when the info box is dismissed
                        pane.InputIndexSet(None)
                        
                    Layout.Inst().PushDialogue(InfoDialogue(
                        Lang('Password Change Failed: ')+Lang(e)))
                    
                else:
                    Layout.Inst().PopDialogue()
                    Layout.Inst().PushDialogue(InfoDialogue( successMessage))
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
            
class DNSDialogue(Dialogue):
    def __init__(self, inLayout, inParent):
        Dialogue.__init__(self, inLayout, inParent)
        data=Data.Inst()
        pane = self.NewPane(DialoguePane(self.parent))
        pane.TitleSet(Lang("DNS Configuration"))
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
        pane = self.Pane()
        pane.ResetFields()
        
        pane.AddTitleField(Lang("Add or Remove Nameserver Entries"))
        pane.AddMenuField(self.addRemoveMenu)
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK") , Lang("<Esc>") : Lang("Cancel") } )
    
    def UpdateFieldsADD(self):
        pane = self.Pane()
        pane.ResetFields()
        
        pane.AddTitleField(Lang("Please Enter the Nameserver IP Address"))
        pane.AddInputField(Lang("IP Address", 16),'0.0.0.0', 'address')
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK") , Lang("<Esc>") : Lang("Cancel") } )
        if pane.CurrentInput() is None:
            pane.InputIndexSet(0)

    def UpdateFieldsREMOVE(self):
        pane = self.Pane()
        pane.ResetFields()
        
        pane.AddTitleField(Lang("Select Nameserver Entry To Remove"))
        pane.AddMenuField(self.removeMenu)
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK") , Lang("<Esc>") : Lang("Cancel") } )
        
    def UpdateFields(self):
        self.Pane().ResetPosition()
        getattr(self, 'UpdateFields'+self.state)() # Despatch method named 'UpdateFields'+self.state
    
    def HandleKeyINITIAL(self, inKey):
        return self.addRemoveMenu.HandleKey(inKey)
     
    def HandleKeyADD(self, inKey):
        handled = True
        pane = self.Pane()
        if pane.CurrentInput() is None:
            pane.InputIndexSet(0)
        if inKey == 'KEY_ENTER':
            inputValues = pane.GetFieldValues()
            Layout.Inst().PopDialogue()
            data=Data.Inst()
            ipaddr = inputValues['address']
            if not IPUtils.ValidateIP(ipaddr):
                Layout.Inst().PushDialogue(InfoDialogue(Lang('Configuration Failed: Invalid IP address')))
            else:
                servers = data.dns.nameservers([])
                servers.append(ipaddr)
                data.NameserversSet(servers)
                self.Commit(Lang("Nameserver")+" "+ ipaddr +" "+Lang("added"))

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
            Layout.Inst().PopDialogue()
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
            Layout.Inst().PopDialogue()
            Data.Inst().NameserversSet([])
            self.Commit(Lang("All nameserver entries deleted"))

    def HandleRemoveChoice(self,  inChoice):
        Layout.Inst().PopDialogue()
        data=Data.Inst()
        servers = data.dns.nameservers([])
        thisServer = servers[inChoice]
        del servers[inChoice]
        data.NameserversSet(servers)
        self.Commit(Lang("Nameserver")+" "+thisServer+" "+Lang("deleted"))
    
    def Commit(self, inMessage):
        try:
            Data.Inst().SaveToResolvConf()
            Layout.Inst().PushDialogue(InfoDialogue( inMessage))
        except Exception, e:
            Layout.Inst().PushDialogue(InfoDialogue( Lang("Update failed: ")+Lang(e)))

# Hostname dialogue no longer used
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
            'fields' : [ [Lang("Timeout (minutes)", 20), FirstValue(State.Inst().AuthTimeoutMinutes(), 5), 'timeout'] ]
            }
        InputDialogue.__init__(self, inLayout, inParent)

    def HandleCommit(self, inValues):
        try:
            timeoutMinutes = int(inValues['timeout'])
        except Exception, e:
            raise Exception("Invalid value - please supply a numeric value")
        
        Auth.Inst().TimeoutSecondsSet(timeoutMinutes * 60)
        return Lang('Timeout Change Successful'), Lang("Timeout changed to ")+inValues['timeout']+Language.Quantity(" minute",  timeoutMinutes)+'.'
        
class BugReportDialogue(InputDialogue):
    def __init__(self, inLayout, inParent):
        self.custom = {
            'title' : Lang("Upload Bug Report"),
            'info' : Lang("Please enter the destination server name, and proxy name if required (blank for none).  Use the form ftp://username:password@server:port for authenticated servers and proxies."), 
            'fields' : [
                [Lang("Destination", 14), Config.Inst().FTPServer(), 'destination'],
                [Lang("Filename", 14), FileUtils.BugReportFilename(), 'filename'],
                [Lang("Proxy", 14), '', 'proxy']
            ]
        }
        InputDialogue.__init__(self, inLayout, inParent)

    def HandleCommit(self, inValues):
        Layout.Inst().TransientBanner(Lang("Uploading Bug Report..."))
            
        hostRef = ShellUtils.MakeSafeParam(Data.Inst().host.uuid(''))
        destServer = ShellUtils.MakeSafeParam(inValues['destination'])
        if not re.match(r'(ftp|http|https)://', destServer):
            raise Exception(Lang('Destination name must start with ftp://, http:// or https://'))
        destFilename = ShellUtils.MakeSafeParam(inValues['filename'])
        destURL = destServer.rstrip('/')+'/'+destFilename.lstrip('/')
        proxy = ShellUtils.MakeSafeParam(inValues['proxy'])
        
        command = "/opt/xensource/bin/xe host-bugreport-upload host='"+hostRef+"' url='"+destURL+"'"
        if proxy != '':
            command += " http_proxy='"+proxy+"'"
            
        status, output = commands.getstatusoutput(command)
                
        if status != 0:
            raise Exception(output) 

        return (Lang("Bug Report Uploaded Sucessfully"), None)
        
class SyslogDialogue(InputDialogue):
    def __init__(self, inLayout, inParent):
        self.custom = {
            'title' : Lang("Change Logging Destination"),
            'info' : Lang("Please enter the hostname or IP address for remote logging (or blank for none)"), 
            'fields' : [ [Lang("Destination", 20), Data.Inst().host.logging.syslog_destination(''), 'destination'] ]
            }
        InputDialogue.__init__(self, inLayout, inParent)

    def HandleCommit(self, inValues):
        Layout.Inst().PushDialogue(BannerDialogue( Lang("Setting Logging Destination...")))
        Layout.Inst().Refresh()
        Layout.Inst().DoUpdate()
        
        Data.Inst().LoggingDestinationSet(inValues['destination'])
        Data.Inst().Update()
        
        Layout.Inst().PopDialogue()
        
        if inValues['destination'] == '':
            message = Lang("Remote logging disabled.")
        else:
            message = Lang("Logging destination set to '")+inValues['destination'] + "'."
        return Lang('Logging Destination Change Successful'), message        

class NTPDialogue(Dialogue):
    def __init__(self, inLayout, inParent):
        Dialogue.__init__(self, inLayout, inParent)

        data=Data.Inst()
            
        choiceDefs = [
            ChoiceDef(Lang("Enable NTP time synchronization"), lambda: self.HandleInitialChoice('ENABLE') ), 
            ChoiceDef(Lang("Disable NTP time synchronization"), lambda: self.HandleInitialChoice('DISABLE') ),
            ChoiceDef(Lang("Add an NTP server"), lambda: self.HandleInitialChoice('ADD') ) ]
        
        if len(data.ntp.servers([])) > 0:
            choiceDefs.append(ChoiceDef(Lang("Remove a single NTP server"), lambda: self.HandleInitialChoice('REMOVE') ))
            choiceDefs.append(ChoiceDef(Lang("Remove all NTP servers"), lambda: self.HandleInitialChoice('REMOVEALL') ))
            
        if Auth.Inst().IsTestMode():
            # Show Status is a testing-only function
            choiceDefs.append(ChoiceDef(Lang("Show Status (ntpstat)"), lambda: self.HandleInitialChoice('STATUS') ))
            
        self.ntpMenu = Menu(self, None, Lang("Configure Network Time"), choiceDefs)
    
        self.ChangeState('INITIAL')
        
    def BuildPane(self):
        if self.state == 'REMOVE':
            choiceDefs = []
            for server in Data.Inst().ntp.servers([]):
                choiceDefs.append(ChoiceDef(server, lambda: self.HandleRemoveChoice(self.removeMenu.ChoiceIndex())))
        
            self.removeMenu = Menu(self, None, Lang("Remove NTP Server"), choiceDefs)
            
        pane = self.NewPane(DialoguePane(self.parent))
        pane.TitleSet(Lang("Configure Network Time"))
        pane.AddBox()
        self.UpdateFields()
        
    def UpdateFieldsINITIAL(self):
        pane = self.Pane()
        pane.ResetFields()
        
        pane.AddTitleField(Lang("Please Select an Option"))
        pane.AddMenuField(self.ntpMenu)
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
    
    def UpdateFieldsADD(self):
        pane = self.Pane()
        pane.ResetFields()
        
        pane.AddTitleField(Lang("Please Enter the NTP Server Name or Address"))
        pane.AddWrappedTextField(Lang("NTP servers supplied by DHCP may overwrite values configured here."))
        pane.NewLine()
        pane.AddInputField(Lang("Server", 16), '', 'name')
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK") , Lang("<Esc>") : Lang("Cancel") } )
        if pane.CurrentInput() is None:
            pane.InputIndexSet(0)

    def UpdateFieldsREMOVE(self):
        pane = self.Pane()
        pane.ResetFields()
        
        pane.AddTitleField(Lang("Select Server Entry To Remove"))
        pane.AddWrappedTextField(Lang("NTP servers supplied by DHCP may overwrite values configured here."))
        pane.NewLine()
        
        pane.AddMenuField(self.removeMenu)
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
        
    def UpdateFields(self):
        self.Pane().ResetPosition()
        getattr(self, 'UpdateFields'+self.state)() # Despatch method named 'UpdateFields'+self.state
    
    def ChangeState(self, inState):
        self.state = inState
        self.BuildPane()
    
    def HandleKeyINITIAL(self, inKey):
        return self.ntpMenu.HandleKey(inKey)
     
    def HandleKeyADD(self, inKey):
        handled = True
        pane = self.Pane()
        if pane.CurrentInput() is None:
            pane.InputIndexSet(0)
        if inKey == 'KEY_ENTER':
            inputValues = pane.GetFieldValues()
            Layout.Inst().PopDialogue()
            data=Data.Inst()
            servers = data.ntp.servers([])
            servers.append(inputValues['name'])
            data.NTPServersSet(servers)
            self.Commit(Lang("NTP server")+" "+inputValues['name']+" "+Lang("added"))
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
            Layout.Inst().PopDialogue()
            handled = True

        return handled
            
    def HandleInitialChoice(self,  inChoice):
        data = Data.Inst()
        try:
            if inChoice == 'ENABLE':
                Layout.Inst().TransientBanner(Lang("Enabling..."))
                data.EnableNTP()
                Layout.Inst().PushDialogue(InfoDialogue( Lang("NTP Time Synchronization Enabled")))
            elif inChoice == 'DISABLE':
                Layout.Inst().TransientBanner(Lang("Disabling..."))
                data.DisableNTP()
                Layout.Inst().PushDialogue(InfoDialogue( Lang("NTP Time Synchronization Disabled")))
            elif inChoice == 'ADD':
                self.ChangeState('ADD')
            elif inChoice == 'REMOVE':
                self.ChangeState('REMOVE')
            elif inChoice == 'REMOVEALL':
                Layout.Inst().PopDialogue()
                data.NTPServersSet([])
                self.Commit(Lang("All server entries deleted"))
            elif inChoice == 'STATUS':
                message = data.NTPStatus()+Lang("\n\n(Initial synchronization may take several minutes)")
                Layout.Inst().PushDialogue(InfoDialogue( Lang("NTP Status"), message))

        except Exception, e:
            Layout.Inst().PushDialogue(InfoDialogue( Lang("Operation Failed"), Lang(e)))
            
        data.Update()

    def HandleRemoveChoice(self,  inChoice):
        Layout.Inst().PopDialogue()
        data=Data.Inst()
        servers = data.ntp.servers([])
        thisServer = servers[inChoice]
        del servers[inChoice]
        data.NTPServersSet(servers)
        self.Commit(Lang("NTP server")+" "+thisServer+" "+Lang("deleted"))
        data.Update()

    def Commit(self, inMessage):
        data=Data.Inst()
        try:
            data.SaveToNTPConf()
            if data.chkconfig.ntpd(False):
                Layout.Inst().TransientBanner(Lang("Restarting NTP daemon with new configuration..."))
                data.RestartNTP()
            Layout.Inst().PushDialogue(InfoDialogue( inMessage))
        except Exception, e:
            Layout.Inst().PushDialogue(InfoDialogue( Lang("Update failed: ")+Lang(e)))

        data.Update()


class TimezoneDialogue(Dialogue):
    def __init__(self, inLayout, inParent):
        Dialogue.__init__(self, inLayout, inParent)

        data=Data.Inst()
            
        choiceDefs = []
        
        continents = data.timezones.continents({})
        keys = sorted(continents.keys())
        
        for key in keys:
            choiceDefs.append(ChoiceDef(key, lambda: self.HandleContinentChoice(continents[keys[self.continentMenu.ChoiceIndex()]]) ))
        
        self.continentMenu = Menu(self, None, Lang("Select Continent"), choiceDefs)
    
        self.ChangeState('INITIAL')
        
    def BuildPane(self):
        if self.state == 'CITY':
            self.cityList = []
            choiceDefs = []
            cityExp = re.compile(self.continentChoice)
            keys = Data.Inst().timezones.cities({}).keys()
            keys.sort()
            for city in keys:
                if cityExp.match(city):
                    self.cityList.append(city)
                    choiceDefs.append(ChoiceDef(city, lambda: self.HandleCityChoice(self.cityMenu.ChoiceIndex())))
        
            if len(choiceDefs) == 0:
                choiceDefs.append(Lang('<None available>'), None)
        
            self.cityMenu = Menu(self, None, Lang("Select City"), choiceDefs)
            
        pane = self.NewPane(DialoguePane(self.parent))
        pane.TitleSet(Lang("Set Timezone"))
        pane.AddBox()
        self.UpdateFields()
        
    def UpdateFieldsINITIAL(self):
        pane = self.Pane()
        pane.ResetFields()
        
        pane.AddTitleField(Lang("Please Select Your Region"))
        pane.AddMenuField(self.continentMenu, 11) # There are 11 'continents' so make this menu 11 high
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
    
    def UpdateFieldsCITY(self):
        pane = self.Pane()
        pane.ResetFields()
        
        pane.AddTitleField(Lang("Please Choose a City Within Your Timezone"))
        pane.AddMenuField(self.cityMenu)
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK") , Lang("<Esc>") : Lang("Cancel") } )
        
    def UpdateFields(self):
        self.Pane().ResetPosition()
        getattr(self, 'UpdateFields'+self.state)() # Despatch method named 'UpdateFields'+self.state
    
    def ChangeState(self, inState):
        self.state = inState
        self.BuildPane()
    
    def HandleKeyINITIAL(self, inKey):
        return self.continentMenu.HandleKey(inKey)
     
    def HandleKeyCITY(self, inKey):
        return self.cityMenu.HandleKey(inKey)
        
    def HandleKey(self, inKey):
        handled = False
        if hasattr(self, 'HandleKey'+self.state):
            handled = getattr(self, 'HandleKey'+self.state)(inKey)
        
        if not handled and inKey == 'KEY_ESCAPE':
            Layout.Inst().PopDialogue()
            handled = True

        return handled
            
    def HandleContinentChoice(self,  inChoice):
        self.continentChoice = inChoice
        self.ChangeState('CITY')

    def HandleCityChoice(self,  inChoice):
        city = self.cityList[inChoice]
        data=Data.Inst()
        Layout.Inst().PopDialogue()
        try:
            data.TimezoneSet(city)
            message = Lang('The timezone has been set to ')+city +".\n\nLocal time is now "+data.CurrentTimeString()
            Layout.Inst().PushDialogue(InfoDialogue( Lang('Timezone Set'), message))
        except Exception, e:
            Layout.Inst().PushDialogue(InfoDialogue( Lang("Configuration failed: ")+Lang(e)))

        data.Update()

class KeyboardDialogue(Dialogue):
    def __init__(self, inLayout, inParent):
        Dialogue.__init__(self, inLayout, inParent)

        data=Data.Inst()
            
        choiceDefs = []
        
        namesToMaps = data.keyboard.namestomaps({})
        names = sorted(namesToMaps.keys())
        for name in names:
            choiceDefs.append(ChoiceDef(name, lambda: self.HandleNameChoice(namesToMaps[names[self.layoutMenu.ChoiceIndex()]]) ))

        choiceDefs.append(ChoiceDef(Lang('Choose Keymap File Directly'), lambda: self.HandleNameChoice(None)))

        self.layoutMenu = Menu(self, None, Lang("Select Keyboard Layout"), choiceDefs)

        choiceDefs = []
        
        keymaps = data.keyboard.keymaps({})
        keys = sorted(keymaps.keys())
        
        for key in keys:
            choiceDefs.append(ChoiceDef(key, lambda: self.HandleKeymapChoice(keys[self.keymapMenu.ChoiceIndex()]) ))
        
        self.keymapMenu = Menu(self, None, Lang("Select Keymap File"), choiceDefs)
    
        self.ChangeState('INITIAL')
        
    def BuildPane(self):            
        pane = self.NewPane(DialoguePane(self.parent))
        pane.TitleSet(Lang("Keyboard Language and Layout"))
        pane.AddBox()
        self.UpdateFields()
        
    def UpdateFieldsINITIAL(self):
        pane = self.Pane()
        pane.ResetFields()
        
        pane.AddTitleField(Lang("Please Select Your Keyboard Layout"))
        pane.AddMenuField(self.layoutMenu, 12) # There are a lot of names so make this menu high
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
            
    def UpdateFieldsKEYMAP(self):
        pane = self.Pane()
        pane.ResetFields()
        
        pane.AddTitleField(Lang("Please Select Your Keymap Name"))
        pane.AddMenuField(self.keymapMenu, 12) # There are a lot of keymaps so make this menu high
        pane.NewLine()
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
            
    def UpdateFields(self):
        self.Pane().ResetPosition()
        getattr(self, 'UpdateFields'+self.state)() # Despatch method named 'UpdateFields'+self.state
    
    def ChangeState(self, inState):
        self.state = inState
        self.BuildPane()
    
    def HandleKeyINITIAL(self, inKey):
        return self.layoutMenu.HandleKey(inKey)
     
    def HandleKeyKEYMAP(self, inKey):
        return self.keymapMenu.HandleKey(inKey)
     
    def HandleKey(self, inKey):
        handled = False
        if hasattr(self, 'HandleKey'+self.state):
            handled = getattr(self, 'HandleKey'+self.state)(inKey)
        
        if not handled and inKey == 'KEY_ESCAPE':
            Layout.Inst().PopDialogue()
            handled = True

        return handled
    
    def HandleNameChoice(self, inChoice):
        if inChoice is None:
            self.ChangeState('KEYMAP')
        else:
            try:
                self.Commit(inChoice)
            except Exception, e:
                Layout.Inst().PushDialogue(InfoDialogue( Lang("Missing keymap: ")+Lang(e)))
            
    def HandleKeymapChoice(self, inChoice):
        self.Commit(inChoice)
    
    def Commit(self, inKeymap):
        data=Data.Inst()
        Layout.Inst().PopDialogue()

        try:
            data.KeymapSet(inKeymap)
            message = Lang('Keyboard type set to ')+data.KeymapToName(inKeymap)
            Layout.Inst().PushDialogue(InfoDialogue( message))
        except Exception, e:
            Layout.Inst().PushDialogue(InfoDialogue( Lang("Configuration failed: ")+Lang(e)))

        data.Update()

class ClaimSRDialogue(Dialogue):
    def __init__(self, inLayout, inParent):
        Dialogue.__init__(self, inLayout, inParent)

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
            self.ChangeState('REBOOT')

class RemoteDBDialogue(Dialogue):
    def __init__(self, inLayout, inParent):
        Dialogue.__init__(self, inLayout, inParent)

        self.useMenu = Menu(self, None, Lang("Choose Option"), [
            ChoiceDef(Lang("Use existing database"), lambda: self.HandleUseChoice('USE')),
            ChoiceDef(Lang("Format disk and create new database"), lambda: self.HandleUseChoice('FORMAT')),
            ChoiceDef(Lang("Cancel"), lambda: self.HandleUseChoice('CANCEL'))
        ] )            

        self.ChangeState('WARNING')

    def IQNString(self, inIQN, inLUN = None):
        if inLUN is None or int(inLUN) > 999: # LUN not present or more than 3 characters
            retVal = "TGPT %-4.4s %-60.60s" % (inIQN.tgpt[:4], inIQN.name[:60])
        else:
            retVal = "TGPT %-4.4s %-52.52s LUN %-3.3s" % (inIQN.tgpt[:4], inIQN.name[:52], str(inLUN)[:3])
        
        return retVal

    def BuildPaneBase(self):
        pane = self.NewPane(DialoguePane(self.parent))
        pane.TitleSet(Lang("Remote Database Configuration"))
        pane.AddBox()
    
    def BuildPaneWARNING(self):
        self.BuildPaneBase()
        self.UpdateFields()
    
    def BuildPaneINITIAL(self):
        self.BuildPaneBase()
        self.UpdateFields()
    
    def BuildPaneREMOVECURRENT(self):
        self.BuildPaneBase()
        self.UpdateFields()
    
    def BuildPaneCHOOSEIQN(self):
        self.BuildPaneBase()

        choiceDefs = []
        
        for iqn in self.probedIQNs:
            choiceDefs.append(ChoiceDef(self.IQNString(iqn), lambda: self.HandleIQNChoice(self.iqnMenu.ChoiceIndex())))

        if len(choiceDefs) == 0:
            choiceDefs.append(ChoiceDef("<No IQNs discovered>", lambda: None))
            
        self.iqnMenu = Menu(self, None, Lang("Select IQN"), choiceDefs)

        self.UpdateFields()

    def BuildPaneCHOOSELUN(self):
        self.BuildPaneBase()

        choiceDefs = []
        
        for lun in self.probedLUNs:
            choiceDefs.append(ChoiceDef("LUN "+str(lun), lambda: self.HandleLUNChoice(self.lunMenu.ChoiceIndex())))

        if len(choiceDefs) == 0:
            choiceDefs.append(ChoiceDef("<No LUNs discovered>", lambda: None))
            
        self.lunMenu = Menu(self, None, Lang("Select LUN"), choiceDefs)

        self.UpdateFields()

    def BuildPaneCREATEDB(self):
        self.BuildPaneBase()
        self.UpdateFields()
        
    def BuildPaneUSEDB(self):
        self.BuildPaneBase()
        self.UpdateFields()
    
    def ChangeState(self, inState):
        self.state = inState
        getattr(self, 'BuildPane'+self.state)() # Despatch method named 'BuildPane'+self.state
        
    def UpdateFieldsWARNING(self):
        pane = self.Pane()
        pane.ResetFields()
        
        pane.AddWarningField(Lang("WARNING"))
        pane.AddWrappedBoldTextField(Lang("Please ensure that no Virtual Machines are running on this host "
            "before continuing.  If this host is in a Pool, the remote database should be configured "
            "only on the Pool master.  The specified remote database iSCSI LUN must be configured on "
            "no more than one host at all times, must not be used for any other purpose, and will not be "
            "usable as a Storage Repository."
            ))
        pane.AddKeyHelpField( { Lang("<F8>") : Lang("Continue"), Lang("<Esc>") : Lang("Cancel") } )        

    def UpdateFieldsINITIAL(self):
        pane = self.Pane()
        data = Data.Inst()
        pane.ResetFields()
        
        pane.AddWrappedTextField(Lang("Please enter the configuration details.  Leave the hostname blank to specify no remote database."))
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
    
    def UpdateFieldsREMOVECURRENT(self):
        pane = self.Pane()
        pane.ResetFields()
        
        pane.AddWrappedBoldTextField(Lang("The current remote database must be removed before a new configuration "
            "can be entered.  Would you like to proceed?"))
        pane.AddKeyHelpField( { Lang("<F8>") : Lang("Remove Current Remote Database"), Lang("<Esc>") : Lang("Cancel") } )
    
    def UpdateFieldsCHOOSEIQN(self):
        pane = self.Pane()
        pane.ResetFields()
        
        pane.AddTitleField(Lang("Please select from the list of discovered IQNs"))
        pane.AddMenuField(self.iqnMenu)
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )

    def UpdateFieldsCHOOSELUN(self):
        pane = self.Pane()
        pane.ResetFields()
        
        pane.AddTitleField(Lang("Please select a LUN from the chosen IQN"))
        pane.AddMenuField(self.lunMenu)
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
            
    def UpdateFieldsCREATEDB(self):
        pane = self.Pane()
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
        pane = self.Pane()
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
        self.Pane().ResetPosition()
        getattr(self, 'UpdateFields'+self.state)() # Despatch method named 'UpdateFields'+self.state
    
    def HandleKeyWARNING(self, inKey):
        handled = False
        
        if inKey == 'KEY_F(8)':
            if Data.Inst().remotedb.is_on_remote_storage(False):
                self.ChangeState('REMOVECURRENT')
            else:
                self.ChangeState('INITIAL')
            handled = True
            
        return handled
    
    def HandleKeyINITIAL(self, inKey):
        handled = True
        pane = self.Pane()

        if inKey == 'KEY_ENTER':
            if not pane.IsLastInput():
                pane.ActivateNextInput()
            else:
                self.newConf = pane.GetFieldValues()
                if self.newConf['remotehost'] == '':
                    self.HandleUseChoice('REMOVE')
                else:
                    try:
                        Layout.Inst().TransientBanner(Lang("Probing for IQNs..."))
                        self.probedIQNs = RemoteDB.Inst().ProbeIQNs(self.newConf)
                        self.ChangeState('CHOOSEIQN')
                    except Exception, e:
                        Layout.Inst().PushDialogue(InfoDialogue( Lang("Failed: ")+Lang(e)))
                    
        elif inKey == 'KEY_TAB':
            pane.ActivateNextInput()
        elif inKey == 'KEY_BTAB':
            pane.ActivatePreviousInput()
        elif pane.CurrentInput().HandleKey(inKey):
            pass # Leave handled as True
        else:
            handled = False
        return handled

    def HandleKeyREMOVECURRENT(self, inKey):
        handled = False
        
        if inKey == 'KEY_F(8)':
            Layout.Inst().TransientBanner(Lang("Removing current database..."))
            Data.Inst().StopXAPI()
            try:
                try:
                    RemoteDB.Inst().ConfigureNoDB()
                    self.ChangeState('INITIAL')
                except Exception, e:
                    Layout.Inst().PopDialogue()
                    Layout.Inst().PushDialogue(InfoDialogue( Lang("Failed: ")+Lang(e)))
            finally:
                Data.Inst().StartXAPI()
                Data.Inst().Update()
            handled = True
            
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
            Layout.Inst().TransientBanner(Lang("Formatting..."))
            Data.Inst().StopXAPI()
            try:
                try:
                    self.dbPresent = RemoteDB.Inst().FormatLUN(self.newConf, self.chosenIQN, self.chosenLUN)
                    Layout.Inst().PopDialogue()
                    Layout.Inst().PushDialogue(InfoDialogue(
                        Lang("Format, Creation, and Configuration Successful")))
                except Exception, e:
                    Layout.Inst().PushDialogue(InfoDialogue( Lang("Failed: ")+Lang(e)))
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
            Layout.Inst().PopDialogue()
            handled = True

        return handled
        
    def HandleIQNChoice(self, inChoice):
        if inChoice is None:
            self.ChangeState('CUSTOMIQN')
        else:
            Layout.Inst().TransientBanner(Lang("Probing for LUNs..."))
            self.chosenIQN = self.probedIQNs[inChoice]
            try:
                self.probedLUNs = RemoteDB.Inst().ProbeLUNs(self.newConf, self.chosenIQN)
            except Exception, e:
                self.probedLUNs = []
        
            self.ChangeState('CHOOSELUN')

    def HandleLUNChoice(self, inChoice):
        if inChoice is None:
            self.ChangeState('CUSTOMLUN')
        else:
            Layout.Inst().TransientBanner(Lang("Scanning target LUN..."))
            
            self.chosenLUN = self.probedLUNs[inChoice]

            self.dbPresent = RemoteDB.Inst().TestLUN(self.newConf, self.chosenIQN, self.chosenLUN)
            
            if self.dbPresent or self.dbPresent is None:
                self.ChangeState('USEDB')
            else:
                self.ChangeState('CREATEDB')

    def HandleUseChoice(self, inChoice):
        if inChoice == 'USE':
            Layout.Inst().TransientBanner(Lang("Configuring Remote Database..."))
            Data.Inst().StopXAPI()
            try:
                try:
                    self.dbPresent = RemoteDB.Inst().ReadyForUse(self.newConf, self.chosenIQN, self.chosenLUN)
                    Layout.Inst().PopDialogue()
                    Layout.Inst().PushDialogue(InfoDialogue(
                        Lang("Configuration Successful")))
                except Exception, e:
                    Layout.Inst().PushDialogue(InfoDialogue( Lang("Failed: ")+Lang(e)))
            finally:
                Data.Inst().StartXAPI()
                Data.Inst().Update()
        elif inChoice == 'REMOVE':
            Layout.Inst().TransientBanner(Lang("Configuring for Operation Without a Remote Database..."))
            Data.Inst().StopXAPI()
            try:
                try:
                    self.dbPresent = RemoteDB.Inst().ConfigureNoDB()
                    Layout.Inst().PopDialogue()
                    Layout.Inst().PushDialogue(InfoDialogue(
                        Lang("Configuration Successful")))
                except Exception, e:
                    Layout.Inst().PushDialogue(InfoDialogue( Lang("Failed: ")+Lang(e)))
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

        pane = self.NewPane(DialoguePane(self.parent))
        pane.TitleSet(Lang("Configure Remote Shell"))
        pane.AddBox()

        self.remoteShellMenu = Menu(self, None, Lang("Configure Remote Shell"), [
            ChoiceDef(Lang("Enable"), lambda: self.HandleChoice(True) ), 
            ChoiceDef(Lang("Disable"), lambda: self.HandleChoice(False) )
            ])
    
        self.UpdateFields()
        
    def UpdateFields(self):
        pane = self.Pane()
        pane.ResetFields()
        
        pane.AddTitleField(Lang("Please select an option"))
        pane.AddMenuField(self.remoteShellMenu)
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )

    def HandleKey(self, inKey):
        handled = self.remoteShellMenu.HandleKey(inKey)
        
        if not handled and inKey == 'KEY_ESCAPE':
            Layout.Inst().PopDialogue()
            handled = True

        return handled
                
    def HandleChoice(self,  inChoice):
        data = Data.Inst()
        Layout.Inst().PopDialogue()
        
        try:
            data.ConfigureRemoteShell(inChoice)
            message = Lang("Configuration Successful")
            if inChoice:
                ShellPipe(['/etc/init.d/sshd', 'start']).Call()
            else:
                ShellPipe(['/etc/init.d/sshd', 'stop']).Call()
                
                if ShellPipe(['/sbin/pidof', 'sshd']).CallRC() == 0: # If PIDs are available
                    message = Lang("New connections via the remote shell are now disabled, but there are "
                        "ssh connections still ongoing.  If necessary, use 'killall sshd' from the Local "
                        "Command Shell to terminate them.")

            Layout.Inst().PushDialogue(InfoDialogue(message))

        except Exception, e:
            Layout.Inst().PushDialogue(InfoDialogue( Lang("Failed: ")+Lang(e)))


class VerboseBootDialogue(Dialogue):
    def __init__(self, inLayout, inParent):
        Dialogue.__init__(self, inLayout, inParent)
        pane = self.NewPane(DialoguePane(self.parent))
        pane.TitleSet(Lang("Configure Verbose Boot Mode"))
        pane.AddBox()

        self.remoteShellMenu = Menu(self, None, Lang("Configure Verbose Boot Mode"), [
            ChoiceDef(Lang("Enable"), lambda: self.HandleChoice(True) ), 
            ChoiceDef(Lang("Disable"), lambda: self.HandleChoice(False) )
            ])
    
        self.UpdateFields()
        
    def UpdateFields(self):
        pane = self.Pane()
        pane.ResetFields()
        
        pane.AddTitleField(Lang("Please select an option"))
        pane.AddMenuField(self.remoteShellMenu)
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )

    def HandleKey(self, inKey):
        handled = self.remoteShellMenu.HandleKey(inKey)
        
        if not handled and inKey == 'KEY_ESCAPE':
            Layout.Inst().PopDialogue()
            handled = True

        return handled
                
    def HandleChoice(self, inChoice):
        data = Data.Inst()
        Layout.Inst().PopDialogue()
        Layout.Inst().TransientBanner(Lang("Updating..."))
        
        try:
            data.SetVerboseBoot(inChoice)
        except Exception, e:
            Layout.Inst().PushDialogue(InfoDialogue( Lang("Failed: ")+Lang(e)))
        else:
            Layout.Inst().PushDialogue(InfoDialogue( Lang("Configuration Updated")))

class ResetDialogue(Dialogue):
    def __init__(self, inLayout, inParent):
        Dialogue.__init__(self, inLayout, inParent)

        self.ChangeState('INITIAL')
        
    def BuildPaneBase(self):
        pane = self.NewPane(DialoguePane(self.parent))
        pane.TitleSet(Lang("Reset to Factory Defaults"))
        pane.AddBox()
    
    def BuildPaneINITIAL(self):
        self.BuildPaneBase()
        self.UpdateFields()

    def BuildPaneCONFIRM(self):
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
        pane.AddWrappedTextField(Lang("This function will delete ALL configuration information, ALL virtual machines "
            "and ALL information within Storage Repositories on local disks.  "
            "This operation cannot be undone.  Do you want to continue?"))
        pane.AddKeyHelpField( { Lang("<F8>") : Lang("Continue"), Lang("<Esc>") : Lang("Cancel") } )

    def UpdateFieldsCONFIRM(self):
        pane = self.Pane()
        pane.ResetFields()
        
        pane.AddWrappedBoldTextField(Lang("Press <Enter> to confirm that you want to reset configuration data and "
            "erase all information in Storage Repositories on local disks.  "
            "The data cannot be recovered after this step."))

        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("Reset to Factory Defaults"), Lang("<Esc>") : Lang("Cancel") } )

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
            self.ChangeState('CONFIRM')
            handled = True
            
        return handled
        
    def HandleKeyCONFIRM(self, inKey):
        handled = False
        
        if inKey == 'KEY_ENTER':
            self.DoAction()
            handled = True
            
        return handled

    def DoAction(self):
        Layout.Inst().ExitBannerSet(Lang("Resetting..."))
        Layout.Inst().SubshellCommandSet("/opt/xensource/libexec/revert-to-factory yesimeanit && sleep 2")
        Data.Inst().SetVerboseBoot(False)
        State.Inst().RebootMessageSet(Lang("This server must reboot to complete the reset process.  Reboot the server now?"))

class ValidateDialogue(Dialogue):
    def __init__(self, inLayout, inParent):
        Dialogue.__init__(self, inLayout, inParent)

        data = Data.Inst()

        pane = self.NewPane(DialoguePane(self.parent))
        
        pane.TitleSet(Lang("Validate Server Configuration"))
        pane.AddBox()
    
        if 'vmx' not in data.cpuinfo.flags([]) and 'svm' not in data.cpuinfo.flags([]):
            self.vtResult = Lang("Not Present on CPU")
        else:
            self.vtResult = Lang("Disabled in BIOS")
            for capability in data.host.capabilities([]):
                if re.match(r'hvm', capability):
                    self.vtResult = Lang("OK")
        
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
        pane = self.Pane()
        pane.ResetFields()
        
        pane.AddTitleField(Lang("Validation Results"))
        pane.AddStatusField(Lang("VT enabled on CPU", 50), self.vtResult)
        pane.AddStatusField(Lang("Local default Storage Repository", 50), self.srResult)
        pane.AddStatusField(Lang("Management network interface", 50), self.netResult)
        
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK") } )

    def HandleKey(self, inKey):
        handled = False
        if inKey == 'KEY_ENTER' or inKey == 'KEY_ESCAPE':
            Layout.Inst().PopDialogue()
            handled = True

        return handled

class SRDialogue(Dialogue):
    def __init__(self, inLayout, inParent):
        Dialogue.__init__(self, inLayout, inParent)

        self.ChangeState('INITIAL')
    
    def Custom(self, inKey):
        return self.custom.get(inKey, None)
    
    def BuildPaneBase(self):
        pane = self.NewPane(DialoguePane(self.parent))
        pane.TitleSet(self.Custom('title'))
        pane.AddBox()
    
    def BuildPaneINITIAL(self):
        data = Data.Inst()
        
        self.choices = SRUtils.SRList(self.Custom('mode'), self.Custom('capabilities'))
        choiceDefs = []
        for choice in self.choices:
            choiceDefs.append(ChoiceDef(choice.name, lambda: self.HandleSRChoice(self.srMenu.ChoiceIndex()) ) )

        if len(choiceDefs) == 0:
            choiceDefs.append(ChoiceDef(Lang('<No suitable SRs available>'), lambda: None)) # Avoid empty menu

        self.srMenu = Menu(self, None, Lang("Select SR"), choiceDefs)

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
        
        pane.AddTitleField(self.Custom('prompt'))
        pane.AddMenuField(self.srMenu)
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )

    def HandleKey(self, inKey):
        handled = False
        if hasattr(self, 'HandleKey'+self.state):
            handled = getattr(self, 'HandleKey'+self.state)(inKey)
        
        if not handled and inKey == 'KEY_ESCAPE':
            Layout.Inst().PopDialogue()
            handled = True

        return handled
        
    def HandleKeyINITIAL(self, inKey):
        handled = self.srMenu.HandleKey(inKey)
        
        if not handled and inKey == 'KEY_F(5)':
            Data.Inst().Update()
            self.BuildPaneINITIAL() # Updates menu
            Layout.Inst().Refresh()
            handled = True
        
        return handled

    def HandleSRChoice(self, inChoice):
        self.DoAction(self.choices[inChoice].sr)
    
class SuspendSRDialogue(SRDialogue):
    def __init__(self, inLayout, inParent):

        self.custom = {
            'title' : Lang("Select Storage Repository for Suspend"),
            'prompt' : Lang("Please select a Storage Repository"),
            'mode' : 'rw',
            'capabilities' : 'vdi_create'
        }
        SRDialogue.__init__(self, inLayout, inParent) # Must fill in self.custom before calling __init__
        
    def DoAction(self, inSR):
        success = False
        
        Layout.Inst().PopDialogue()
        try:
            Data.Inst().SuspendSRSet(inSR)
            Layout.Inst().PushDialogue(InfoDialogue( Lang('Configuration Successful'),
                Lang("Suspend SR set to '"+inSR['name_label']+"'")))
        except Exception, e:
            Layout.Inst().PushDialogue(InfoDialogue( Lang("Configuration failed: ")+str(e)))
        Data.Inst().Update()

class CrashDumpSRDialogue(SRDialogue):
    def __init__(self, inLayout, inParent):

        self.custom = {
            'title' : Lang("Select Storage Repository for Crash Dumps"),
            'prompt' : Lang("Please select a Storage Repository"),
            'mode' : 'rw',
            'capabilities' : 'vdi_create'
        }
        SRDialogue.__init__(self, inLayout, inParent) # Must fill in self.custom before calling __init__
        
    def DoAction(self, inSR):
        success = False
        
        Layout.Inst().PopDialogue()
        try:
            Data.Inst().CrashDumpSRSet(inSR)
            Layout.Inst().PushDialogue(InfoDialogue( Lang('Configuration Successful'),
                Lang("Crash Dump SR set to '"+inSR['name_label']+"'")))
        except Exception, e:
            Layout.Inst().PushDialogue(InfoDialogue( Lang("Configuration failed: ")+str(e)))
        Data.Inst().Update()


class PatchDialogue(FileDialogue):
    def __init__(self, inLayout, inParent):

        self.custom = {
            'title' : Lang("Apply Software Upgrade"),
            'searchregexp' : r'.*\.xbk$',  # Type of backup file is .xbk
            'deviceprompt' : Lang("Select the device containing the upgrade"), 
            'fileprompt' : Lang("Select the upgrade file"),
            'confirmprompt' : Lang("Press <F8> to begin the upgrade process"),
            'mode' : 'ro'
        }
        FileDialogue.__init__(self, inLayout, inParent) # Must fill in self.custom before calling __init__
        
    def DoAction(self):
        success = False
        
        Layout.Inst().PopDialogue()
        
        Layout.Inst().PushDialogue(BannerDialogue(
            Lang("Applying upgrade... This make take several minutes.  Press <Ctrl-C> to abort.")))
            
        try:
            try:
                Layout.Inst().Refresh()
                Layout.Inst().DoUpdate()
                
                hostRef = Data.Inst().host.uuid(None)
                if hostRef is None:
                    raise Exception("Internal error 1")
                    
                filename = self.vdiMount.MountedPath(self.filename)
                FileUtils.AssertSafePath(filename)
                command = "/opt/xensource/bin/xe update-upload file-name='"+filename+"' host-uuid="+hostRef
                status, output = commands.getstatusoutput(command)
                
                if status != 0:
                    raise Exception(output)
                
                Layout.Inst().PopDialogue()
                Layout.Inst().PushDialogue(InfoDialogue(
                    Lang("Upgrade Successful"), Lang("Please reboot to use the newly installed software.")))

            except Exception, e:
                Layout.Inst().PopDialogue()
                Layout.Inst().PushDialogue(InfoDialogue( Lang("Software Upgrade Failed"), Lang(e)))
                
        finally:
            try:
                self.PreExitActions()
            except Exception, e:
                Layout.Inst().PushDialogue(InfoDialogue( Lang("Software Upgrade Failed"), Lang(e)))

class BackupDialogue(FileDialogue):
    def __init__(self, inLayout, inParent):

        self.custom = {
            'title' : Lang("Backup Server State"),
            'searchregexp' : r'.*\.xbk$',  # Type of backup file is .xbk
            'deviceprompt' : Lang("Select the backup device"), 
            'fileprompt' : Lang("Choose the backup filename"),
            'filename' : 'backup.xbk',
            'confirmprompt' : Lang("Press <F8> to begin the backup process"),
            'mode' : 'rw'
        }
        FileDialogue.__init__(self, inLayout, inParent) # Must fill in self.custom before calling __init__
        
    def DoAction(self):
        filename = self.vdiMount.MountedPath(self.filename)
        if os.path.isfile(filename):
            Layout.Inst().PushDialogue(QuestionDialogue(
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
        
        Layout.Inst().PopDialogue()
        
        Layout.Inst().PushDialogue(BannerDialogue(
            Lang("Saving to backup... This make take several minutes.  Press <Ctrl-C> to abort.")))
            
        try:
            try:
                Layout.Inst().Refresh()
                Layout.Inst().DoUpdate()
                
                hostRef = Data.Inst().host.uuid(None)
                if hostRef is None:
                    raise Exception("Internal error 1")
                    
                filename = self.vdiMount.MountedPath(self.filename)
                FileUtils.AssertSafePath(filename)
                command = "/opt/xensource/bin/xe host-backup file-name='"+filename+"' host="+hostRef
                status, output = commands.getstatusoutput(command)
                
                if status != 0:
                    raise Exception(output)
                
                Layout.Inst().PopDialogue()
                Layout.Inst().PushDialogue(InfoDialogue(
                    Lang("Backup Successful")))

            except Exception, e:
                Layout.Inst().PopDialogue()
                Layout.Inst().PushDialogue(InfoDialogue( Lang("Backup Failed"), Lang(e)))
                
        finally:
            try:
                self.PreExitActions()
            except Exception, e:
                Layout.Inst().PushDialogue(InfoDialogue( Lang("Backup Failed"), Lang(e)))

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
        
        Layout.Inst().PopDialogue()
        
        Layout.Inst().PushDialogue(BannerDialogue(
            Lang("Restoring from backup... This may take several minutes.")))
            
        try:
            try:
                Layout.Inst().Refresh()
                Layout.Inst().DoUpdate()
                
                hostRef = Data.Inst().host.uuid(None)
                if hostRef is None:
                    raise Exception("Internal error 1")
                    
                filename = self.vdiMount.MountedPath(self.filename)
                FileUtils.AssertSafePath(filename)
                command = "/opt/xensource/bin/xe host-restore file-name='"+filename+"' host="+hostRef
                status, output = commands.getstatusoutput(command)
                
                if status != 0:
                    raise Exception(output)
                
                Layout.Inst().PopDialogue()
                Layout.Inst().PushDialogue(InfoDialogue(
                    Lang("Restore Successful"), Lang("Please reboot to use the new backup.")))

            except Exception, e:
                Layout.Inst().PopDialogue()
                Layout.Inst().PushDialogue(InfoDialogue( Lang("Restore Failed"), Lang(e)))
                
        finally:
            try:
                self.PreExitActions()
            except Exception, e:
                Layout.Inst().PushDialogue(InfoDialogue( Lang("Restore Failed"), Lang(e)))

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
        
        Layout.Inst().PopDialogue()
        
        Layout.Inst().PushDialogue(BannerDialogue(
            Lang("Installing License...")))
            
        try:
            try:
                Layout.Inst().Refresh()
                Layout.Inst().DoUpdate()
                
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
                Layout.Inst().PopDialogue()
                Layout.Inst().PushDialogue(InfoDialogue(
                    Lang("License Installed Successfully")))

            except Exception, e:
                Layout.Inst().PopDialogue()
                Layout.Inst().PushDialogue(InfoDialogue( Lang("License Installation Failed"), Lang(e)))
                
        finally:
            try:
                self.PreExitActions()
            except Exception, e:
                Layout.Inst().PushDialogue(InfoDialogue( Lang("License Installation Failed"), Lang(e)))

class SaveBugReportDialogue(FileDialogue):
    def __init__(self, inLayout, inParent):
        self.custom = {
            'title' : Lang("Save Bug Report"),
            'searchregexp' : r'.*',  # Type of bugtool file is .tar
            'deviceprompt' : Lang("Select The Destination Device"), 
            'fileprompt' : Lang("Choose A Destination Filename"),
            'filename' : FileUtils.BugReportFilename(),
            'confirmprompt' : Lang("Press <F8> To Save The Bug Report"),
            'mode' : 'rw'
        }
        FileDialogue.__init__(self, inLayout, inParent) # Must fill in self.custom before calling __init__
        
    def DoAction(self):
        success = False
        
        Layout.Inst().PopDialogue()
        
        Layout.Inst().PushDialogue(BannerDialogue(
            Lang("Saving Bug Report...")))
            
        try:
            try:
                Layout.Inst().Refresh()
                Layout.Inst().DoUpdate()

                filename = self.vdiMount.MountedPath(self.filename)
                FileUtils.AssertSafePath(filename)

                file = open(filename, "w")
                # xen-bugtool requires a value for $USER
                command = "( export USER=root && /usr/sbin/xen-bugtool --yestoall --silent --output=tar --outfd="+str(file.fileno()) + ' )'
                status, output = commands.getstatusoutput(command)
                file.close()

                if status != 0:
                    raise Exception(output)

                Layout.Inst().PopDialogue()
                Layout.Inst().PushDialogue(InfoDialogue(
                    Lang("Saved Bug Report")))

            except Exception, e:
                Layout.Inst().PopDialogue()
                Layout.Inst().PushDialogue(InfoDialogue( Lang("Save Failed"), Lang(e)))
                
        finally:
            try:
                self.PreExitActions()
            except Exception, e:
                Layout.Inst().PushDialogue(InfoDialogue( Lang("Save Failed"), Lang(e)))

class TestNetworkDialogue(Dialogue):
    def __init__(self, inLayout, inParent):
        Dialogue.__init__(self, inLayout, inParent)

        pane = self.NewPane(DialoguePane(self.parent))
        pane.TitleSet(Lang("Test Network Configuration"))
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
        self.Pane().ResetPosition()
        getattr(self, 'UpdateFields'+self.state)() # Despatch method named 'UpdateFields'+self.state
        
    def UpdateFieldsINITIAL(self):
        pane = self.Pane()
        pane.ResetFields()
        
        pane.AddTitleField(Lang("Select Test"))
        pane.AddMenuField(self.testMenu)
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
        
    def UpdateFieldsCUSTOM(self):
        pane = self.Pane()
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
            Layout.Inst().PopDialogue()
            handled = True

        return handled
        
    def HandleKeyINITIAL(self, inKey):
        handled = self.testMenu.HandleKey(inKey)
        if not handled and inKey == 'KEY_LEFT':
            Layout.Inst().PopDialogue()
            handled = True
        return handled
        
    def HandleKeyCUSTOM(self, inKey):
        handled = True
        pane = self.Pane()
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
            self.Pane().InputIndexSet(0)
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
            Layout.Inst().PushDialogue(InfoDialogue( Lang("Ping successful"), output))
        else:
            Layout.Inst().PushDialogue(InfoDialogue( Lang("Ping failed"), output))
        
