
from XSConsoleAuth import *
from XSConsoleBases import *
from XSConsoleCurses import *
from XSConsoleData import *
from XSConsoleDialoguePane import *
from XSConsoleDialogues import *
from XSConsoleFields import *
from XSConsoleLang import *
from XSConsoleMenus import *

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
        inPane.AddTitleField(Lang("Change Password"))
    
        inPane.AddWrappedTextField(Lang("Press <Enter> to change the password for user 'root'.  "
        "If this host is in a pool, this will change the password of the pool master."))

    def UpdateFieldsCHANGETIMEOUT(self, inPane):
        inPane.AddTitleField(Lang("Change Auto-Logoff Time"))
    
        inPane.AddWrappedTextField(Lang("The current auto-logoff time is ") +
            str(State.Inst().AuthTimeoutMinutes()) + ' minutes.  '+
            Lang("Users will be automatically logged out after there has been no activity for this time.  "+
                "Press <Enter> to change this timeout.")
        )

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
        elif inName == 'DIALOGUE_CHANGETIMEOUT':
            self.AuthenticatedOnly(lambda: self.layout.PushDialogue(ChangeTimeoutDialogue(self.layout, self.parent)))
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
        self.layout.SubshellCommandSet("/bin/bash --login")
            
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
        
