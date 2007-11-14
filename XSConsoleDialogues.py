
from XSConsoleAuth import *
from XSConsoleBases import *
from XSConsoleCurses import *
from XSConsoleData import *
from XSConsoleFields import *
from XSConsoleLang import *
from XSConsoleMenus import *

from pprint import pprint

class DialoguePane:
    LEFT_XSTART = 1
    TITLE_XSTART = LEFT_XSTART
    TITLE_YSTART = 1
    
    def __init__(self, inXPos, inYPos, inXSize, inYSize, inParent = None):
        self.window = CursesWindow(inXPos, inYPos, inXSize, inYSize, inParent)
        self.xSize = inXSize
        self.ySize = inYSize
        self.xOffset = 0
        self.yOffset = 0
        self.ResetFields()
        self.ResetPosition()
    
    def ResetFields(self):
        self.fields = {}
        self.inputFields = []
        self.inputIndex = None

    def Win(self):
        return self.window

    def AddBox(self):
        if not self.window.HasBox():
            self.window.AddBox()
            self.xSize -= 2
            self.ySize -= 2
            self.xOffset += 1
            self.yOffset += 1
            self.ResetPosition()

    def ActivateNextInput(self): 
        self.InputIndexSet((self.inputIndex + 1) % len(self.inputFields))
            
    def ActivatePreviousInput(self): 
        self.InputIndexSet((self.inputIndex + len(self.inputFields) - 1) % len(self.inputFields))
            
    def IsLastInput(self):
        return self.inputIndex + 1 == len(self.inputFields)

    def CurrentInput(self):
        if self.inputIndex is not None:
            fieldName = self.inputFields[self.inputIndex]
            retVal = self.fields[fieldName].fieldObj
        else:
            retVal = None
        return retVal

    def InputIndexSet(self, inIndex):
        if self.inputIndex is not None:
            self.CurrentInput().Deactivate()
        
        self.inputIndex = inIndex
        
        if self.inputIndex is not None:
            self.CurrentInput().Activate()

    def NeedsCursor(self):
        if self.inputIndex is not None:
            retVal = True
        else:
            retVal = False
        return retVal

    def CursorOff(self):
        self.window.CursorOff()
        
    def GetFieldValues(self):
        retVal = {}
        for fieldName in self.inputFields:
            retVal[fieldName] = self.fields[fieldName].fieldObj.Content()
        return retVal

    def Refresh(self):
        self.Win().Refresh();

    def ColoursSet(self, inBase, inBright, inHighlight = None, inTitle = None):
        self.baseColour = inBase
        self.brightColour = inBright
        self.highlightColour = inHighlight or inBright
        self.titleColour = inTitle or inBright
        self.window.DefaultColourSet(self.baseColour)
        self.window.Redraw()

    def ResetPosition(self, inXPos = None, inYPos = None):
        self.xPos = self.xOffset + FirstValue(inXPos, self.TITLE_XSTART)
        self.yPos = self.yOffset + FirstValue(inYPos, self.TITLE_YSTART)
        self.xStart = self.xPos

    def MakeLabel(self, inLabel = None):
        if inLabel:
            retVal = inLabel
        else:
            # Generate unique but repeatable label
            retVal = str(self.xPos) + ',' +str(self.yPos)
        return retVal

    def AddField(self, inObj, inTag = None):
        self.fields[inTag or self.MakeLabel()] = Struct(xpos = self.xPos, ypos = self.yPos, fieldObj = inObj)
        self.xPos += inObj.Width()
        return inObj

    def NewLine(self, inNumLines = None):
        self.xPos = self.xStart
        self.yPos += inNumLines or 1

    def AddTitleField(self, inTitle):
        self.AddField(TextField(inTitle, self.titleColour))
        self.NewLine(2)
        
    def AddTextField(self, inText):
        self.AddField(TextField(inText, self.baseColour))
        self.NewLine()
    
    def AddWrappedTextField(self, inText):
        width = self.window.xSize - self.xPos - 1
        field = self.AddField(WrappedTextField(str(inText), width, self.baseColour))
        self.NewLine(field.Height())

    def AddWrappedBoldTextField(self, inText):
        width = self.window.xSize - self.xPos - 1
        field = self.AddField(WrappedTextField(str(inText), width, self.brightColour))
        self.NewLine(field.Height())

    def AddStatusField(self, inName, inValue):
        self.AddField(TextField(str(inName), self.brightColour))
        width = self.window.xSize - self.xPos - 1
        field = self.AddField(WrappedTextField(str(inValue), width, self.baseColour))
        self.NewLine(field.Height())
    
    def AddInputField(self, inName, inValue, inLabel):
        self.AddField(TextField(str(inName), self.brightColour))
        self.AddField(InputField(str(inValue), self.highlightColour), inLabel)
        self.inputFields.append(inLabel)
        self.NewLine()
    
    def AddPasswordField(self, inName, inValue, inLabel):
        self.AddField(TextField(str(inName), self.brightColour))
        passwordField = InputField(str(inValue), self.highlightColour)
        passwordField.HideText()
        self.AddField(passwordField, inLabel)        
        self.inputFields.append(inLabel)
        self.NewLine()
    
    def AddMenuField(self, inMenu):
        field = self.AddField(MenuField(inMenu, self.baseColour, self.highlightColour))
        self.NewLine(field.Height() + 1)
    
    def AddKeyHelpField(self, inKeys):
        (oldXPos, oldYPos) = (self.xPos, self.yPos)
        self.xPos = self.xOffset + 1
        self.yPos = self.yOffset + self.ySize - 1
        for name in sorted(inKeys):
            self.AddField(TextField(str(name), self.brightColour))
            self.xPos += 1
            self.AddField(TextField(str(inKeys[name]), self.baseColour))
            self.xPos += 1

        (self.xPos, self.yPos) = (oldXPos, oldYPos)
    
    def Render(self):
        self.window.Erase()
        for field in self.fields.values():
            field.fieldObj.Render(self.window, field.xpos, field.ypos)
        self.window.Refresh()
            
    def Delete(self):
        self.window.Delete()

class RootDialogue(Dialogue):
    
    def __init__(self, inLayout, inParent):
        Dialogue.__init__(self, inLayout, inParent);
        menuPane = self.NewPane('menu', DialoguePane(1, 2, 38, 21, self.parent))
        menuPane.ColoursSet('MENU_BASE', 'MENU_BRIGHT', 'MENU_HIGHLIGHT')
        statusPane = self.NewPane('status', DialoguePane(41, 2, 38, 21, self.parent))
        statusPane.ColoursSet('HELP_BASE', 'HELP_BRIGHT')
        self.menu = RootMenu(self)
        self.currentStatus = 'STATUS'
        self.UpdateFields()

    def UpdateFieldsSTATUS(self, inPane):
        data = Data.Inst()

        inPane.AddWrappedTextField(data.dmi.system_manufacturer())
        inPane.AddWrappedTextField(data.dmi.system_product_name())
        inPane.NewLine()
        inPane.AddWrappedTextField(data.host.software_version.product_brand() + ' ' +
            data.host.software_version.product_version())
        inPane.NewLine()
        inPane.AddTitleField(Lang("Management Network Parameters"))
        
        if len(data.derived.managementpifs([])) == 0:
            inPane.AddTextField(Lang("<No network configured>"))
        else:
            for pif in data.derived.managementpifs():
                inPane.AddStatusField(Lang('IP address', 16), data.host.address()) # FIXME: should come from pif
                if pif['ip_configuration_mode'].lower().startswith('static'):
                    inPane.AddStatusField(Lang('Netmask', 16),  pif['netmask'])
                    inPane.AddStatusField(Lang('Gateway', 16),  pif['gateway'])
        inPane.NewLine()
    
    def UpdateFieldsPROPERTIES(self, inPane):

        inPane.AddTitleField(Lang("System Properties"))
    
        inPane.AddWrappedTextField(Lang(
            "Press <Enter> to view the properties of this system."))
    
    def UpdateFieldsAUTH(self, inPane):

        inPane.AddTitleField(Lang("Authentication"))
    
        if Auth.Inst().IsAuthenticated():
            username = Auth.Inst().LoggedInUsername()
        else:
            username = "<none>"

        inPane.AddStatusField(Lang("User", 14), username)
        inPane.NewLine()
        
        if Auth.Inst().IsAuthenticated():
            inPane.AddWrappedTextField(Lang("You are logged in.  Press <Enter> to access the authentication menu."))
        else:
            inPane.AddWrappedTextField(Lang(
                "You are currently not logged in. Press <Enter> to log in with your username and password to access privileged operations."))

    def UpdateFieldsLOGOFF(self, inPane):
        inPane.AddTitleField(Lang("Log Off"))
    
        inPane.AddWrappedTextField(Lang("Press <Enter> to log off."))

    def UpdateFieldsCHANGEPASSWORD(self, inPane):
        inPane.AddTitleField(Lang("Log Off"))
    
        inPane.AddWrappedTextField(Lang("Press <Enter> to change the password for user 'root'.  "
        "If this host is in a pool, this will change the password of the pool master."))


    def UpdateFieldsINTERFACE(self, inPane):
        inPane.AddTitleField(Lang("Management Interface"))
    
        inPane.AddWrappedTextField(Lang(
            "The management interface is a network interface used to control this host remotely.  "
            "Press <Enter> to configure."))
        
    def UpdateFieldsXENSERVER(self, inPane):
        data = Data.Inst()

        inPane.AddTitleField(Lang("XenServer"))
        inPane.AddStatusField(Lang("Name", 16), str(data.host.software_version.product_brand()))
        inPane.AddStatusField(Lang("Version", 16), str(data.host.software_version.product_version()))
        inPane.AddStatusField(Lang("Build Number", 16), str(data.host.software_version.build_number()))
        inPane.AddStatusField(Lang("Kernel Version", 16), str(data.host.software_version.linux()))
        inPane.AddStatusField(Lang("Xen Version", 16), str(data.host.software_version.xen()))
        inPane.NewLine()
    
    def UpdateFieldsLICENCE(self, inPane):
        data = Data.Inst()

        expiryStr = data.host.license_params.expiry()
        if (re.match('\d{8}', expiryStr)):
            # Convert ISO date to more readable form
            expiryStr = expiryStr[0:4]+'-'+expiryStr[4:6]+'-'+expiryStr[6:8]
        
        inPane.AddTitleField(Lang("License"))
        inPane.AddStatusField(Lang("Product SKU", 16), str(data.host.license_params.sku_type()))
        inPane.AddStatusField(Lang("Expiry", 16), expiryStr)
        inPane.AddStatusField(Lang("Sockets", 16), str(data.host.license_params.sockets()))
        inPane.NewLine()
        inPane.AddTitleField(Lang("Product Code"))
        inPane.AddWrappedTextField(str(data.host.license_params.productcode()))
        inPane.NewLine()
        inPane.AddTitleField(Lang("Serial Number"))
        inPane.AddWrappedTextField(str(data.host.license_params.serialnumber()))

    def UpdateFieldsHOST(self, inPane):
        data = Data.Inst()

        inPane.AddTitleField(Lang("Hostname"))
        inPane.AddWrappedTextField(data.host.hostname())
        inPane.NewLine()

    def UpdateFieldsSYSTEM(self, inPane):
        data = Data.Inst()

        inPane.AddTitleField(Lang("System Manufacturer"))
        inPane.AddWrappedTextField(data.host.software_version.oem_manufacturer())
        inPane.NewLine()
        
        inPane.AddTitleField(Lang("System Model"))
        inPane.AddWrappedTextField(data.host.software_version.oem_model())
        inPane.NewLine()
        
        inPane.AddTitleField(data.host.software_version.machine_serial_name(Lang("Serial Number")))
        inPane.AddWrappedTextField(data.host.software_version.machine_serial_number())
        inPane.NewLine()
        
        inPane.AddTitleField(Lang("Asset Tag"))
        inPane.AddWrappedTextField(data.dmi.asset_tag(Lang("None"))) # FIXME: Get from XenAPI
        inPane.NewLine()

    def UpdateFieldsPROCESSOR(self, inPane):
        data = Data.Inst()

        inPane.AddTitleField(Lang("Processor Details"))
        
        inPane.AddStatusField(Lang("Logical CPUs", 27), str(len(data.host.host_CPUs([]))))
        inPane.AddStatusField(Lang("Populated CPU Sockets", 27), str(data.dmi.cpu_populated_sockets()))
        inPane.AddStatusField(Lang("Total CPU Sockets", 27), str(data.dmi.cpu_sockets()))

        inPane.NewLine()
        inPane.AddTitleField(Lang("Description"))
        
        for name, value in data.derived.cpu_name_summary().iteritems():
            inPane.AddWrappedTextField(str(value)+" x "+name)
    
    def UpdateFieldsMEMORY(self, inPane):
        data = Data.Inst()
        
        inPane.AddTitleField(Lang("System Memory"))
            
        inPane.AddStatusField(Lang("Total memory", 27), str(data.dmi.memory_size())+' MB')
        inPane.AddStatusField(Lang("Populated memory sockets", 27), str(data.dmi.memory_modules()))
        inPane.AddStatusField(Lang("Total memory sockets", 27), str(data.dmi.memory_sockets()))

    def UpdateFieldsSTORAGE(self, inPane):
        data = Data.Inst()
        
        inPane.AddTitleField(Lang("Local Storage Controllers"))
        
        for name in data.lspci.storage_controllers([]):
            inPane.AddWrappedTextField(name)
            inPane.NewLine()
            
    def UpdateFieldsPIF(self, inPane):
        data = Data.Inst()
        
        inPane.AddTitleField(Lang("Physical Network Interfaces"))
        
        for pif in data.host.PIFs([]):
            inPane.AddWrappedBoldTextField(pif['metrics']['device_name'])
            if pif['metrics']['carrier']:
                inPane.AddTextField(Lang("(connected)"))
            else:
                inPane.AddTextField(Lang("(not connected)"))
                
            inPane.AddStatusField(Lang("MAC Address", 16), pif['MAC'])
            inPane.AddStatusField(Lang("Device", 16), pif['device'])
            inPane.NewLine()

    def UpdateFieldsBMC(self, inPane):
        data = Data.Inst()
        
        inPane.AddTitleField(Lang("BMC Information"))
        
        inPane.AddStatusField(Lang("BMC Firmware Version",  22), data.bmc.version())
        
    def UpdateFieldsCPLD(self, inPane):
        data = Data.Inst()
        
        inPane.AddTitleField(Lang("CPLD Information"))

        inPane.AddTextField(Lang("Not available"))

    def UpdateFieldsBIOS(self, inPane):
        data = Data.Inst()
        
        inPane.AddTitleField(Lang("BIOS Information"))
        
        inPane.AddStatusField(Lang("Vendor", 12), data.dmi.bios_vendor())
        inPane.AddStatusField(Lang("Version", 12), data.dmi.bios_version())

    def UpdateFieldsSELECTNIC(self, inPane):
        data = Data.Inst()
        
        inPane.AddTitleField(Lang("Current Management Interface"))
        
        if len(data.derived.managementpifs([])) == 0:
            inPane.AddTextField(Lang("<No interface configured>"))
        else:
            for pif in data.derived.managementpifs([]):
                inPane.AddStatusField(Lang('Device', 16), pif['device'])
                inPane.AddStatusField(Lang('MAC Address', 16),  pif['MAC'])
                inPane.AddStatusField(Lang('Assigned IP', 16),  data.host.address()) # FIXME: should come from pif
                inPane.AddStatusField(Lang('DHCP/Static IP', 16),  pif['ip_configuration_mode'])
                if pif['ip_configuration_mode'].lower().startswith('static'):
                    # inPane.AddStatusField(Lang('IP Address', 16),  pif['IP'])
                    inPane.AddStatusField(Lang('Netmask', 16),  pif['netmask'])
                    inPane.AddStatusField(Lang('Gateway', 16),  pif['gateway'])
                
                inPane.NewLine()
                inPane.AddTitleField(Lang("NIC Vendor"))
                inPane.AddWrappedTextField(pif['metrics']['vendor_name'])
                inPane.NewLine()
                inPane.AddTitleField(Lang("NIC Model"))
                inPane.AddWrappedTextField(pif['metrics']['device_name'])
                
        inPane.AddKeyHelpField( {
            Lang("<Enter>") : Lang("Reconfigure this interface")
        })
        
    def UpdateFieldsTESTNETWORK(self, inPane):
        inPane.AddTitleField(Lang("Test Network"))
    
        inPane.AddWrappedTextField(Lang(
            "Press <Enter> to test the configured network interface."))
    
    def UpdateFieldsREBOOT(self, inPane):
        inPane.AddTitleField(Lang("Server Reboot"))
    
        inPane.AddWrappedTextField(Lang(
            "Press <Enter> to reboot this server."))
    
    def UpdateFieldsSHUTDOWN(self, inPane):
        inPane.AddTitleField(Lang("Server Shutdown"))
    
        inPane.AddWrappedTextField(Lang(
            "Press <Enter> to shutdown this server."))
            
    def UpdateFieldsLOCALSHELL(self, inPane):
        inPane.AddTitleField(Lang("Local Command Shell"))
    
        inPane.AddWrappedTextField(Lang(
            "Press <Enter> to start a local command shell on this server."))
 
    def UpdateFieldsDNS(self, inPane):
        data = Data.Inst()
        inPane.AddTitleField(Lang("DNS Servers"))
    
        inPane.AddTitleField(Lang("Current Nameservers"))
        if len(data.dns.nameservers([])) == 0:
            inPane.AddWrappedTextField(Lang("<No nameservers are configured>"))
        for dns in data.dns.nameservers([]):
            inPane.AddWrappedTextField(str(dns))
        inPane.NewLine()
        inPane.AddWrappedTextField(Lang("Changes to this configuration may be overwritten if any "
                                        "interfaces are configured to used DHCP."))
        inPane.AddKeyHelpField( {
            Lang("<Enter>") : Lang("Reconfigure DNS")
        })

    def UpdateFieldsHOSTNAME(self, inPane):
        data = Data.Inst()
        inPane.AddTitleField(Lang("Set Hostname"))
    
        inPane.AddWrappedTextField(Lang("The name of this host is"))
        inPane.NewLine()
        inPane.AddWrappedTextField(data.host.hostname())
        inPane.NewLine()
        inPane.AddWrappedTextField(Lang("Press <Enter> to change the name of this host."))
        inPane.AddKeyHelpField( {
            Lang("<Enter>") : Lang("Configure hostname")
        })

    def UpdateFieldsEXCEPTION(self, inPane,  inException):
        inPane.AddTitleField(Lang("Information not available"))
        inPane.AddWrappedTextField(Lang("You may need to log in to view this information"))
        inPane.AddWrappedTextField(str(inException))

    def UpdateFields(self):
        menuPane = self.Pane('menu')
        menuPane.ResetFields();
        menuPane.ResetPosition();
        menuPane.AddTitleField(self.menu.CurrentMenu().Title())
        menuPane.AddMenuField(self.menu.CurrentMenu())
        statusPane = self.Pane('status')
        try:
            statusPane.ResetFields();
            statusPane.ResetPosition();
            getattr(self, 'UpdateFields'+self.currentStatus)(statusPane) # Despatch method named 'UpdateFields'+self.currentStatus

        except Exception, e:
            statusPane.ResetFields();
            statusPane.ResetPosition();
            self.UpdateFieldsEXCEPTION(statusPane,  e)
        
        keyHash = { Lang("<Up/Down>") : Lang("Select") }
        if self.menu.CurrentMenu().Parent() != None:
            keyHash[ Lang("<Esc/Left>") ] = Lang("Back")
        else:
            keyHash[ Lang("<Enter>") ] = Lang("OK")

        menuPane.AddKeyHelpField( keyHash )
    
    def ChangeStatus(self, inName):
        self.Pane('status').ResetFields()
        self.currentStatus = inName
        self.UpdateFields()
    
    def HandleKey(self, inKey):
        currentMenu = self.menu.CurrentMenu()

        handled = currentMenu.HandleKey(inKey)

        if handled:
            self.UpdateFields();
            self.Pane('menu').Refresh()
            self.Pane('status').Refresh()
            
        return handled

    def ChangeMenu(self, inName):
        self.menu.ChangeMenu(inName)
        self.menu.CurrentMenu().HandleEnter()
    
    def AuthenticatedOnly(self, inFunc):
        if not Auth.Inst().IsAuthenticated():
            self.layout.PushDialogue(LoginDialogue(self.layout, self.parent,
                                                   Lang('Please log in to perform this function'), inFunc))
        else:
            inFunc()
        
    def ActivateDialogue(self, inName):
        if inName == 'DIALOGUE_AUTH':
            if (Auth.Inst().IsAuthenticated()):
                self.ChangeMenu('MENU_AUTH')
            else:
                self.layout.PushDialogue(LoginDialogue(self.layout, self.parent))
        elif inName == 'DIALOGUE_INTERFACE':
            self.AuthenticatedOnly(lambda: self.layout.PushDialogue(InterfaceDialogue(self.layout, self.parent)))
        elif inName == 'DIALOGUE_CHANGEPASSWORD':
            self.AuthenticatedOnly(lambda: self.layout.PushDialogue(ChangePasswordDialogue(self.layout, self.parent)))
        elif inName == 'DIALOGUE_TESTNETWORK':
            self.layout.PushDialogue(TestNetworkDialogue(self.layout,  self.parent))
        elif inName == 'DIALOGUE_DNS':
            self.AuthenticatedOnly(lambda: self.layout.PushDialogue(DNSDialogue(self.layout,  self.parent)))
        elif inName == 'DIALOGUE_HOSTNAME':
            self.AuthenticatedOnly(lambda: self.layout.PushDialogue(HostnameDialogue(self.layout,  self.parent)))
        elif inName == 'DIALOGUE_REBOOT':
            self.AuthenticatedOnly(lambda: self.layout.PushDialogue(QuestionDialogue(self.layout,  self.parent,
                Lang("Do you want to reboot this server?"), lambda x: self.RebootDialogueHandler(x))))
        elif inName == 'DIALOGUE_SHUTDOWN':
            self.AuthenticatedOnly(lambda: self.layout.PushDialogue(QuestionDialogue(self.layout,  self.parent,
                Lang("Do you want to shutdown this server?"), lambda x: self.ShutdownDialogueHandler(x))))
        elif inName == 'DIALOGUE_LOCALSHELL':
            self.AuthenticatedOnly(lambda: self.StartLocalShell())
            
    def StartLocalShell(self):
        user = os.environ.get('USER', 'root')
        self.layout.ExitBannerSet(Lang("\rShell for local user '")+user+"'.\r\r"+
                Lang("Type 'exit' to return to the management console.\r"))
        self.layout.ExitCommandSet("/bin/bash")
            
    def RebootDialogueHandler(self,  inYesNo):
        if inYesNo == 'y':
            self.layout.ExitBannerSet(Lang("Rebooting..."))
            self.layout.ExitCommandSet('/sbin/shutdown -r now')

    def ShutdownDialogueHandler(self,  inYesNo):
        if inYesNo == 'y':
            self.layout.ExitBannerSet(Lang("Shutting down..."))
            self.layout.ExitCommandSet('/sbin/shutdown -h now')

    def HandleLogOff(self):
        name = Auth.Inst().LoggedInUsername()
        Auth.Inst().LogOut()
        Data.Inst().Update()
        self.layout.PushDialogue(InfoDialogue(self.layout, self.parent, Lang("User '")+name+Lang("' logged out")))
        self.ChangeMenu('MENU_ROOT')
        
class LoginDialogue(Dialogue):
    def __init__(self, inLayout, inParent,  inText = None,  inSuccessFunc = None):
        Dialogue.__init__(self, inLayout, inParent);
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
            Lang("<Enter>") : Lang("Next/OK"),
            Lang("<Tab>") : Lang("Next"),
            Lang("<Shift-Tab>") : Lang("Previous")
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
                    self.layout.PushDialogue(InfoDialogue(self.layout, self.parent, Lang('Login Failed: ')+str(e)))

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

class ChangePasswordDialogue(Dialogue):
    def __init__(self, inLayout, inParent,  inText = None,  inSuccessFunc = None):
        Dialogue.__init__(self, inLayout, inParent);
        self.text = inText
        self.successFunc = inSuccessFunc
        if self.text is None:
            paneHeight = 8
        else:
            paneHeight = 10
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
        pane.AddPasswordField(Lang("Old Password", 21), Auth.Inst().DefaultPassword(), 'oldpassword')
        pane.AddPasswordField(Lang("New Password", 21), '', 'newpassword1')
        pane.AddPasswordField(Lang("Repeat New Password", 21), '', 'newpassword2')
        pane.AddKeyHelpField( {
            Lang("<Enter>") : Lang("Next/OK"),
            Lang("<Esc>") : Lang("Cancel"),
            Lang("<Tab>") : Lang("Next"),
            Lang("<Shift-Tab>") : Lang("Previous")
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
                try:
                    if inputValues['newpassword1'] != inputValues['newpassword2']:
                        raise Exception(Lang('New passwords do not match'))
                
                    Data.Inst().ChangePassword(inputValues['oldpassword'], inputValues['newpassword1'])
                    
                except Exception, e:
                    self.layout.PushDialogue(InfoDialogue(self.layout, self.parent,
                        Lang('Password Change Failed'), Lang('Reason: ')+str(e)))
                    
                else:
                    self.layout.PushDialogue(InfoDialogue(self.layout, self.parent, Lang('Password Change Successful')))
                    
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
        Dialogue.__init__(self, inLayout, inParent);
        self.text = inText
        if inInfo is None:
            self.info = None
            paneHeight = 6
            
        else:
            self.info = inInfo
            paneHeight = 7+ len(Language.ReflowText(self.info, 70))
                
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
            pane.ResetPosition(37 - len(self.text) / 2, 1);
        else:
            pane.ResetPosition(3, 1);
        
        pane.AddWrappedBoldTextField(self.text)
        if self.info is not None:
            pane.ResetPosition(1, 3);
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
        Dialogue.__init__(self, inLayout, inParent);
        self.text = inText
        pane = self.NewPane('banner', DialoguePane(3, 9, 74, 5, self.parent))
        pane.ColoursSet('MODAL_BASE', 'MODAL_BRIGHT', 'MODAL_HIGHLIGHT')
        pane.AddBox()
        self.UpdateFields()

    def UpdateFields(self):
        pane = self.Pane('banner')
        pane.ResetFields()
        if len(self.text) < 70:
            # Centre text if short
            pane.ResetPosition(37 - len(self.text) / 2, 1);
        else:
            pane.ResetPosition(30, 1);
        
        pane.AddWrappedBoldTextField(self.text)

class QuestionDialogue(Dialogue):
    def __init__(self, inLayout, inParent, inText,  inHandler):
        Dialogue.__init__(self, inLayout, inParent);
        self.text = inText
        self.handler = inHandler
        pane = self.NewPane('question', DialoguePane(3, 9, 74, 5, self.parent))
        pane.ColoursSet('MODAL_BASE', 'MODAL_BRIGHT', 'MODAL_HIGHLIGHT')
        pane.AddBox()
        self.UpdateFields()

    def UpdateFields(self):
        pane = self.Pane('question')
        pane.ResetFields()
        if len(self.text) < 70:
            # Centre text if short
            pane.ResetPosition(37 - len(self.text) / 2, 1);
        else:
            pane.ResetPosition(30, 1);
        
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
        Dialogue.__init__(self, inLayout, inParent);
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
                pane.AddStatusField(Lang("netmask Mask",  16),  self.netmask)
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
                self.layout.PushDialogue(InfoDialogue(self.layout, self.parent, Lang("Configuration Failed: "+str(e))))
                
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
            data.ReconfigureManagement(pif, self.mode, self.IP,  self.netmask, self.gateway)
            Data.Inst().Update()
            
class DNSDialogue(Dialogue):
    def __init__(self, inLayout, inParent):
        Dialogue.__init__(self, inLayout, inParent);
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
            self.layout.PushDialogue(InfoDialogue(self.layout, self.parent, Lang("Update failed: ")+str(e)))

class HostnameDialogue(Dialogue):
    def __init__(self, inLayout, inParent):
        Dialogue.__init__(self, inLayout, inParent);
        paneHeight = 6
        pane = self.NewPane('hostname', DialoguePane(3, 12 - paneHeight/2, 74, paneHeight, self.parent))
        pane.ColoursSet('MODAL_BASE', 'MODAL_BRIGHT', 'MODAL_HIGHLIGHT')
        pane.Win().TitleSet("Set Hostname")
        pane.AddBox()
        self.UpdateFields()
        pane.InputIndexSet(0)
        
    def UpdateFields(self):
        pane = self.Pane('hostname')
        pane.ResetFields()
        pane.AddInputField(Lang("Hostname", 14), Data.Inst().host.hostname(''), 'hostname')
        pane.AddKeyHelpField( {
            Lang("<Enter>") : Lang("OK"),
            Lang("<Esc>") : Lang("Cancel")
        })
        
    def HandleKey(self, inKey):
        handled = True
        pane = self.Pane('hostname')
        if inKey == 'KEY_ESCAPE':
            self.layout.PopDialogue()
        elif inKey == 'KEY_ENTER':
                inputValues = pane.GetFieldValues()
                self.layout.PopDialogue()
                self.layout.DoUpdate()
                try:
                    Data.Inst().HostnameSet(inputValues['hostname'])
                    self.layout.PushDialogue(InfoDialogue(self.layout, self.parent,
                        Lang('Hostname Change Successful'), Lang("Hostname changed to '")+inputValues['hostname']+"'"))
                except Exception, e:
                    self.layout.PushDialogue(InfoDialogue(self.layout, self.parent, Lang('Failed: ')+str(e)))
                Data.Inst().Update()
        elif pane.CurrentInput().HandleKey(inKey):
            pass # Leave handled as True
        else:
            handled = False
        return True

class TestNetworkDialogue(Dialogue):
    def __init__(self, inLayout, inParent):
        Dialogue.__init__(self, inLayout, inParent);

        paneHeight = 12
        paneHeight = min(paneHeight,  22)
        pane = self.NewPane('testnetwork', DialoguePane(3, 12 - paneHeight/2, 74, paneHeight, self.parent))
        pane.Win().TitleSet(Lang("Test Network Configuration"))
        pane.AddBox()
        
        gatewayName = Data.Inst().ManagementGateway()
        if gatewayName is None: gatewayName = 'Unknown'
        
        self.testMenu = Menu(self, None, Lang("Select Test Type"), [
            ChoiceDef(Lang("Ping local address 127.0.0.1"), lambda: self.HandleTestChoice('local') ), 
            ChoiceDef(Lang("Ping IP gateway address")+" ("+gatewayName+")", lambda: self.HandleTestChoice('gateway') ), 
            ChoiceDef(Lang("Ping www.xensource.com"), lambda: self.HandleTestChoice('xensource') ), 
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
        return self.testMenu.HandleKey(inKey)
        
    def HandleKeyCUSTOM(self, inKey):
        handled = True
        pane = self.Pane('testnetwork')
        if pane.CurrentInput() is None:
            pane.InputIndexSet(0)
        if inKey == 'KEY_ENTER':
            inputValues = pane.GetFieldValues()
            self.customIP = inputValues['address']
            self.DoPing(self.customIP)
            
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
        elif inChoice == 'xensource':
            pingTarget = 'www.xensource.com'
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
                output = str(e)
            
        if success:
            self.layout.PushDialogue(InfoDialogue(self.layout, self.parent, Lang("Ping successful"), output))
        else:
            self.layout.PushDialogue(InfoDialogue(self.layout, self.parent, Lang("Ping failed"), output))
        
