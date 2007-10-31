
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
        self.ResetFields()
        self.ResetPosition()
    
    def ResetFields(self):
        self.fields = {}
        self.inputFields = []
        self.inputIndex = None

    def Win(self):
        return self.window

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
        self.xPos = FirstValue(inXPos, self.TITLE_XSTART)
        self.yPos = FirstValue(inYPos, self.TITLE_YSTART)
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
        self.xPos = 1
        self.yPos = self.ySize - 1
        if self.window.HasBox():
            self.xPos += 1
            self.yPos -= 1
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

class RightPanel:
    @classmethod
    def StatusUpdateFields(cls, inPane):
        data = Data.Inst()

        inPane.AddWrappedTextField(data.dmi.system_manufacturer())
        inPane.AddWrappedTextField(data.dmi.system_product_name())
        inPane.NewLine()
        inPane.AddWrappedTextField(data.host.software_version.product_brand() + ' ' +
            data.host.software_version.product_version())
        inPane.NewLine()
        inPane.AddTitleField(Lang("Management network parameters"))
        
        inPane.AddStatusField(Lang("Interface", 14), data.host.address())
        inPane.AddStatusField(Lang("IP Address", 14), data.GetInfo('host.address'))
        inPane.AddStatusField(Lang("Subnet", 14), data.ManagementSubnet())
        inPane.AddStatusField(Lang("Gateway", 14), data.ManagementGateway())
        inPane.NewLine()
        
    @classmethod
    def PropertiesUpdateFields(cls, inPane):

        inPane.AddTitleField(Lang("System Properties"))
    
        inPane.AddWrappedTextField(Lang(
            "Press enter to view the properties of this system."))
    
    @classmethod
    def AuthUpdateFields(cls, inPane):

        inPane.AddTitleField(Lang("Authentication"))
    
        if Auth.IsLoggedIn():
            username = Auth.LoggedInUsername()
        else:
            username = "<none>"

        inPane.AddStatusField(Lang("User", 14), username)
        inPane.NewLine()
        
        if Auth.IsLoggedIn():
            inPane.AddWrappedTextField(Lang("You are logged in.  Press Enter to log out."))
        else:
            inPane.AddWrappedTextField(Lang(
                "You are currently not logged in. Press Enter to log in with your username and password to access privileged operations."))
    
    @classmethod
    def InterfaceUpdateFields(cls, inPane):
        inPane.AddTitleField(Lang("Management Interface"))
    
        inPane.AddWrappedTextField(Lang(
            "The management interface is a network interface used to control this host remotely.  "
            "Press enter to configure."))
    
    @classmethod
    def XenSourceUpdateFields(cls, inPane):
        data = Data.Inst()

        inPane.AddTitleField(Lang("XenSource"))
        inPane.AddStatusField(Lang("Name", 16), str(data.host.software_version.product_brand()))
        inPane.AddStatusField(Lang("Version", 16), str(data.host.software_version.product_version()))
        inPane.AddStatusField(Lang("Build Number", 16), str(data.host.software_version.build_number()))
        inPane.AddStatusField(Lang("Kernel Version", 16), str(data.host.software_version.linux()))
        inPane.AddStatusField(Lang("Xen Version", 16), str(data.host.software_version.xen()))
        inPane.NewLine()
        
    @classmethod
    def LicenceUpdateFields(cls, inPane):
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
        
    @classmethod
    def HostUpdateFields(cls, inPane):
        data = Data.Inst()

        inPane.AddTitleField(Lang("Hostname"))
        inPane.AddWrappedTextField(data.host.hostname())
        inPane.NewLine()
    
    @classmethod
    def SystemUpdateFields(cls, inPane):
        data = Data.Inst()

        inPane.AddTitleField(Lang("System Manufacturer"))
        inPane.AddWrappedTextField(data.dmi.system_manufacturer())
        inPane.NewLine()
        
        inPane.AddTitleField(Lang("System Model"))
        inPane.AddWrappedTextField(data.dmi.system_product_name())
        inPane.NewLine()
        
        inPane.AddTitleField(Lang("Serial Number/Service Tag"))
        inPane.AddWrappedTextField(data.dmi.system_serial_number())
        inPane.NewLine()
        
        inPane.AddTitleField(Lang("Asset Tag"))
        inPane.AddWrappedTextField(data.dmi.asset_tag())
        inPane.NewLine()
        
    @classmethod
    def ProcessorUpdateFields(cls, inPane):
        data = Data.Inst()

        inPane.AddTitleField(Lang("Processor Details"))
        
        inPane.AddStatusField(Lang("Logical CPUs", 27), str(data.host.host_CPUs.Size()))
        inPane.AddStatusField(Lang("Populated CPU Sockets", 27), str(data.dmi.cpu_populated_sockets()))
        inPane.AddStatusField(Lang("Total CPU Sockets", 27), str(data.dmi.cpu_sockets()))

        inPane.NewLine()
        inPane.AddTitleField(Lang("Description"))
        
        for name, value in data.derived.cpu_name_summary().iteritems():
            inPane.AddWrappedTextField(str(value)+" x "+name)
    
    @classmethod    
    def MemoryUpdateFields(cls, inPane):
        data = Data.Inst()
        
        inPane.AddTitleField(Lang("System Memory"))
            
        inPane.AddStatusField(Lang("Total memory", 27), str(data.dmi.memory_size())+' MB')
        inPane.AddStatusField(Lang("Populated memory sockets", 27), str(data.dmi.memory_modules()))
        inPane.AddStatusField(Lang("Total memory sockets", 27), str(data.dmi.memory_sockets()))
            
    @classmethod    
    def PIFUpdateFields(cls, inPane):
        data = Data.Inst()
        
        inPane.AddTitleField(Lang("Physical Network Interfaces"))
        
        for pif in data.host.PIFs():
            inPane.AddWrappedBoldTextField(pif['metrics']['device_name'])
            if pif['metrics']['carrier']:
                inPane.AddTextField(Lang("(connected)"))
            else:
                inPane.AddTextField(Lang("(not connected)"))
                
            inPane.AddStatusField(Lang("MAC Address:", 16), pif['MAC'])
            inPane.AddStatusField(Lang("Device:", 16), pif['device'])
            inPane.NewLine()
            
    @classmethod    
    def BIOSUpdateFields(cls, inPane):
        data = Data.Inst()
        
        inPane.AddTitleField(Lang("BIOS Information"))
        
        inPane.AddStatusField(Lang("Vendor", 12), data.dmi.bios_vendor())
        inPane.AddStatusField(Lang("Version", 12), data.dmi.bios_version())
            
    @classmethod    
    def SelectNICUpdateFields(cls, inPane):
        data = Data.Inst()
        
        inPane.AddTitleField(Lang("Current Configuration"))
        
        if data.derived.managementpifs.Size() == 0:
            inPane.AddTextField(Lang("<No network configured>"))
        else:
            for pif in data.derived.managementpifs():
                inPane.AddStatusField(Lang('Device', 16), pif['device'])
                inPane.AddStatusField(Lang('MAC Address', 16),  pif['MAC'])
                inPane.AddStatusField(Lang('Assigned IP', 16),  data.host.address()) # FIXME: should come from pif
                inPane.AddStatusField(Lang('DHCP/Static IP', 16),  pif['ip_configuration_mode'])
                inPane.NewLine()
                inPane.AddTitleField(Lang("NIC Vendor"))
                inPane.AddWrappedTextField(pif['metrics']['vendor_name'])
                inPane.NewLine()
                inPane.AddTitleField(Lang("NIC Model"))
                inPane.AddWrappedTextField(pif['metrics']['device_name'])
                
        inPane.AddKeyHelpField( {
            Lang("<Enter>") : Lang("Reconfigure this interface")
        })
            
    @classmethod    
    def ExceptionUpdateFields(cls, inPane,  inException):
        inPane.AddTitleField(Lang("Information not available"))
        inPane.AddWrappedTextField(Lang("You may need to log in to view this information"))
        inPane.AddWrappedTextField(str(inException))
            
class RootDialogue(Dialogue):
    statusUpdaters = {
        'STATUS' : RightPanel.StatusUpdateFields,
        'AUTH' : RightPanel.AuthUpdateFields,
        'INTERFACE' : RightPanel.InterfaceUpdateFields,
        'PROPERTIES' : RightPanel.PropertiesUpdateFields,
        'XENSOURCE' : RightPanel.XenSourceUpdateFields,
        'LICENCE' : RightPanel.LicenceUpdateFields,
        'HOST' : RightPanel.HostUpdateFields,
        'SYSTEM' : RightPanel.SystemUpdateFields,
        'PROCESSOR' : RightPanel.ProcessorUpdateFields,
        'MEMORY' : RightPanel.MemoryUpdateFields,
        'PIF' : RightPanel.PIFUpdateFields,
        'BIOS' : RightPanel.BIOSUpdateFields, 
        'SELECTNIC' : RightPanel.SelectNICUpdateFields
    }

    def __init__(self, inLayout, inParent):
        Dialogue.__init__(self, inLayout, inParent);
        menuPane = self.NewPane('menu', DialoguePane(1, 2, 38, 20, self.parent))
        menuPane.ColoursSet('MENU_BASE', 'MENU_BRIGHT', 'MENU_HIGHLIGHT')
        statusPane = self.NewPane('status', DialoguePane(41, 2, 38, 20, self.parent))
        statusPane.ColoursSet('HELP_BASE', 'HELP_BRIGHT')
        self.menu = RootMenu(self)
        self.currentStatus = 'STATUS'
        self.UpdateFields()

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
            self.statusUpdaters[self.currentStatus](statusPane)
        except Exception, e:
            statusPane.ResetFields();
            statusPane.ResetPosition();
            RightPanel.ExceptionUpdateFields(statusPane,  e)
        
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
            
    def ActivateDialogue(self, inName):
        if (Auth.IsLoggedIn()):
            name = Auth.LoggedInUsername()
            Auth.LogOut()
            Data.Inst().Update()
            self.layout.PushDialogue(InfoDialogue(self.layout, self.parent, Lang("User '")+name+Lang("' logged out")))
        else:
            self.layout.PushDialogue(LoginDialogue(self.layout, self.parent))
        
class LoginDialogue(Dialogue):
    def __init__(self, layout, parent):
        Dialogue.__init__(self, layout, parent);
        pane = self.NewPane('login', DialoguePane(3, 8, 74, 7, self.parent))
        pane.ColoursSet('MODAL_BASE', 'MODAL_BRIGHT', 'MODAL_HIGHLIGHT')
        pane.Win().TitleSet("Login")
        pane.Win().AddBox()
        self.UpdateFields()
        pane.InputIndexSet(0)
        
    def UpdateFields(self):
        menuPane = self.Pane('login')
        menuPane.ResetFields()
        menuPane.ResetPosition(2, 2);
        menuPane.AddInputField(Lang("Username:", 14), "root", 'username')
        menuPane.AddPasswordField(Lang("Password:", 14), "", 'password')
        menuPane.AddKeyHelpField( {
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
            if pane.IsLastInput():
                inputValues = pane.GetFieldValues()
                self.layout.PopDialogue()
                self.layout.DoUpdate()
                success = Auth.ProcessLogin(inputValues['username'], inputValues['password'])
                Data.Inst().Update()

                if success:
                    self.layout.PushDialogue(InfoDialogue(self.layout, self.parent, Lang('Login successful')))
                else:
                    self.layout.PushDialogue(InfoDialogue(self.layout, self.parent, Lang('Login failed: ')+Auth.ErrorMessage()))
                        
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
        return True

class InfoDialogue(Dialogue):
    def __init__(self, inLayout, inParent, inText):
        Dialogue.__init__(self, inLayout, inParent);
        self.text = inText
        pane = self.NewPane('info', DialoguePane(3, 8, 74, 6, self.parent))
        pane.ColoursSet('MODAL_BASE', 'MODAL_BRIGHT', 'MODAL_HIGHLIGHT')
        pane.Win().AddBox()
        self.UpdateFields()

    def UpdateFields(self):
        pane = self.Pane('info')
        pane.ResetFields()
        if len(self.text) < 70:
            # Centre text if short
            pane.ResetPosition(37 - len(self.text) / 2, 2);
        else:
            pane.ResetPosition(30, 2);
        
        pane.AddWrappedBoldTextField(self.text)
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK") } )
        
    def HandleKey(self, inKey):
        handled = True
        if inKey == 'KEY_ESCAPE' or inKey == 'KEY_ENTER':
            self.layout.PopDialogue()
        else:
            handled = False
        return True
