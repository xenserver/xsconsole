
import re

from XSConsoleAuth import *
from XSConsoleBases import *
from XSConsoleConfig import *
from XSConsoleCurses import *
from XSConsoleData import *
from XSConsoleDialoguePane import *
from XSConsoleDialogues import *
from XSConsoleFields import *
from XSConsoleLang import *
from XSConsoleMenus import *

class RootDialogue(Dialogue):
    
    def __init__(self, inLayout, inParent):
        Dialogue.__init__(self, inLayout, inParent)
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
            inPane.AddStatusField(Lang('IP address', 16), data.ManagementIP(''))
            inPane.AddStatusField(Lang('Netmask', 16),  data.ManagementNetmask(''))
            inPane.AddStatusField(Lang('Gateway', 16),  data.ManagementGateway(''))
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
            inPane.AddWrappedTextField(Lang("You are logged in.  Press <Enter> to log out, change the password or alter login characteristics."))
        else:
            inPane.AddWrappedTextField(Lang("You are currently not logged in.  Press <Enter> to access the login menu."))
                


    def UpdateFieldsLOGINOUT(self, inPane):
        if Auth.Inst().IsAuthenticated():
            inPane.AddTitleField(Lang("Log Out"))
            inPane.AddWrappedTextField(Lang("Press <Enter> to log out."))
        else:
            inPane.AddTitleField(Lang("Log In"))
            inPane.AddWrappedTextField(Lang("Press <Enter> to log in."))

    def UpdateFieldsCHANGEPASSWORD(self, inPane):
        inPane.AddTitleField(Lang("Change Password"))
    
        inPane.AddWrappedTextField(Lang("Press <Enter> to change the password for user 'root'.  "
        "If this host is in a pool, this will change the password of the pool master."))

    def UpdateFieldsCHANGETIMEOUT(self, inPane):
        inPane.AddTitleField(Lang("Change Auto-Logout Time"))
    
        timeout = State.Inst().AuthTimeoutMinutes()
        message = Lang("The current auto-logout time is ") + str(timeout) + " "

        message += Language.Quantity("minute", timeout) + ".  "
        message += Lang("Users will be automatically logged out after there has been no activity for this time.  "+
                "Press <Enter> to change this timeout.")
    
        inPane.AddWrappedTextField(message)

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
        inPane.AddWrappedTextField(data.host.name_label())
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
            Lang("<Enter>") : Lang("Reconfigure this interface")
        })
        
    def UpdateFieldsTESTNETWORK(self, inPane):
        inPane.AddTitleField(Lang("Test Network"))
    
        inPane.AddWrappedTextField(Lang(
            "Press <Enter> to test the configured network interface."))
    
    def UpdateFieldsREBOOTSHUTDOWN(self, inPane):
        inPane.AddTitleField(Lang("Reboot/Shutdown"))
    
        inPane.AddWrappedTextField(Lang(
            "Press <Enter> to access the reboot and shutdown menu, or to enter Recovery Mode."))
    
    def UpdateFieldsREBOOT(self, inPane):
        inPane.AddTitleField(Lang("Reboot Server"))
    
        inPane.AddWrappedTextField(Lang(
            "Press <Enter> to reboot this server into normal operating mode."))
    
        inPane.AddKeyHelpField( {
            Lang("<Enter>") : Lang("Reboot Server")
        } )

    def UpdateFieldsRECOVERY(self, inPane):
        inPane.AddTitleField(Lang("Reboot Into Recovery Mode"))
    
        inPane.AddWrappedTextField(Lang(
            "Press <Enter> to reboot this server into recovery mode.  "
            "This mode can also be used to apply updates or patches."))
        
        inPane.AddKeyHelpField( {
            Lang("<Enter>") : Lang("Reboot Into Recovery Mode")
        } )
        
    def UpdateFieldsSHUTDOWN(self, inPane):
        inPane.AddTitleField(Lang("Shutdown Server"))
    
        inPane.AddWrappedTextField(Lang(
            "Press <Enter> to shutdown this server."))
        
        inPane.AddKeyHelpField( {
            Lang("<Enter>") : Lang("Shutdown Server")
        } )
        
    def UpdateFieldsLOCALSHELL(self, inPane):
        inPane.AddTitleField(Lang("Local Command Shell"))
    
        inPane.AddWrappedTextField(Lang(
            "Press <Enter> to start a local command shell on this server."))
 
    def UpdateFieldsBURP(self, inPane):
        inPane.AddTitleField(Lang("Backup, Restore and Update"))
    
        inPane.AddWrappedTextField(Lang(
            "From this menu you can backup and restore the system database, and apply "
            "software updates or patches to the system."))
 
        inPane.AddKeyHelpField( {
            Lang("<Enter>") : Lang("Show Menu")
        } ) 
        
    def UpdateFieldsTECHNICAL(self, inPane):
        inPane.AddTitleField(Lang("Technical Support"))
    
        inPane.AddWrappedTextField(Lang(
            "From the Technical Support menu you can enable local and remote shells, "
            "validate the configuration of this server and upload bug reports."))
 
        inPane.AddKeyHelpField( {
            Lang("<Enter>") : Lang("Technical Support Menu")
        } )
    
    def UpdateFieldsINSTALLLICENCE(self, inPane):
        data = Data.Inst()
        inPane.AddTitleField(Lang("Install License File"))

        inPane.AddWrappedTextField(Lang(
            "Press <Enter> to install a license file from removable media."))
 
        inPane.AddKeyHelpField( {
            Lang("<Enter>") : Lang("Install License")
        } )
    
    def UpdateFieldsREMOTESHELL(self, inPane):
        data = Data.Inst()
        inPane.AddTitleField(Lang("Remote Shell (ssh)"))
    
        if data.chkconfig.sshd() is None:
            message = Lang('unknown.  To enable or disable')
        elif data.chkconfig.sshd():
            message = Lang('enabled.  To disable')
        else:
            message = Lang('disabled.  To enable')
            
        inPane.AddWrappedTextField(Lang(
            "This server can accept a remote login via ssh.  Currently remote login is ") +
            message + Lang(" this feature, press <Enter>."))
 
        inPane.AddKeyHelpField( {
            Lang("<Enter>") : Lang("Configure Remote Shell")
        } )
 
    def UpdateFieldsVALIDATE(self, inPane):
        data = Data.Inst()
        inPane.AddTitleField(Lang("Validate Server Cnfigration"))

        inPane.AddWrappedTextField(Lang(
            "Press <Enter> to check the basic configuration of this server."))
 
        inPane.AddKeyHelpField( {
            Lang("<Enter>") : Lang("Validate")
        } )
        
    def UpdateFieldsPATCH(self, inPane):
        data = Data.Inst()
        inPane.AddTitleField(Lang("Apply Upgrade or Patch"))

        if State.Inst().IsRecoveryMode():
            inPane.AddWrappedTextField(Lang(
                "Press <Enter> to apply a software upgrade or patch."))
            inPane.AddKeyHelpField( { Lang("<Enter>") : Lang("Upgrade or Patch") } )   
        else:
            inPane.AddWrappedTextField(Lang(
                "Please enter Recovery Mode from the Reboot menu before applying an upgrade or patch."))
 
    def UpdateFieldsBACKUP(self, inPane):
        data = Data.Inst()
        inPane.AddTitleField(Lang("Backup Server State"))

        inPane.AddWrappedTextField(Lang(
            "Press <Enter> to backup the server state to a removable device."))
            
        inPane.AddKeyHelpField( { Lang("<Enter>") : Lang("Backup") } )   
 
    def UpdateFieldsRESTORE(self, inPane):
        data = Data.Inst()
        inPane.AddTitleField(Lang("Restore Server State"))

        inPane.AddWrappedTextField(Lang(
            "Press <Enter> to restore the server state from a removable device."))
            
        inPane.AddKeyHelpField( { Lang("<Enter>") : Lang("Restore") } )   
 
    def UpdateFieldsBUGREPORT(self, inPane):
        data = Data.Inst()
        inPane.AddTitleField(Lang("Upload Bug Report"))

        inPane.AddWrappedTextField(Lang(
            "This option will upload a bug report file, containing information about "
            "the state of this machine, to the support server at ")+
            Config.Inst().FTPServer()+Lang(".  This file may contain sensitive data."))
            
        inPane.AddKeyHelpField( { Lang("<Enter>") : Lang("Upload Bug Report") } )  
        
    def UpdateFieldsSAVEBUGREPORT(self, inPane):
        data = Data.Inst()
        inPane.AddTitleField(Lang("Save Bug Report"))

        inPane.AddWrappedTextField(Lang(
            "This option will save a bug report file, containing information about "
            "the state of this machine, to removable media.  This file may contain sensitive data."))
            
        inPane.AddKeyHelpField( { Lang("<Enter>") : Lang("Save Bug Report") } )  
        
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
        inPane.AddWrappedTextField(data.host.name_label())
        inPane.NewLine()
        inPane.AddWrappedTextField(Lang("Press <Enter> to change the name of this host."))
        inPane.AddKeyHelpField( {
            Lang("<Enter>") : Lang("Configure hostname")
        })

    def UpdateFieldsSYSLOG(self, inPane):
        data = Data.Inst()
        inPane.AddTitleField(Lang("Remote Logging (syslog)"))
    
        if data.host.logging.syslog_destination('') == '':
            inPane.AddWrappedTextField(Lang("Remote logging is not configured on this host."))
        else:
            inPane.AddWrappedTextField(Lang("The remote logging destination for this host is"))
            inPane.NewLine()
            inPane.AddWrappedTextField(data.host.logging.syslog_destination())
    
        inPane.AddKeyHelpField( {
            Lang("<Enter>") : Lang("Configure logging")
        })

    def UpdateFieldsEXCEPTION(self, inPane,  inException):
        inPane.AddTitleField(Lang("Information not available"))
        inPane.AddWrappedTextField(Lang("You may need to log in to view this information"))
        inPane.AddWrappedTextField(str(inException))

    def UpdateFields(self):
        menuPane = self.Pane('menu')
        menuPane.ResetFields()
        menuPane.ResetPosition()
        menuPane.AddTitleField(self.menu.CurrentMenu().Title())
        menuPane.AddMenuField(self.menu.CurrentMenu())
        statusPane = self.Pane('status')
        try:
            statusPane.ResetFields()
            statusPane.ResetPosition()
            getattr(self, 'UpdateFields'+self.currentStatus)(statusPane) # Despatch method named 'UpdateFields'+self.currentStatus

        except Exception, e:
            statusPane.ResetFields()
            statusPane.ResetPosition()
            self.UpdateFieldsEXCEPTION(statusPane, e)
        
        keyHash = { Lang("<Up/Down>") : Lang("Select") }
        if self.menu.CurrentMenu().Parent() != None:
            keyHash[ Lang("<Esc/Left>") ] = Lang("Back")
        else:
            keyHash[ Lang("<Enter>") ] = Lang("OK")

        menuPane.AddKeyHelpField( keyHash )
        
        if statusPane.NeedsScroll() and statusPane.NumStaticFields() == 0:
            statusPane.AddKeyHelpField( {
                Lang("<Page Up/Page Down>") : Lang("Scroll")
            })
    
    def ChangeStatus(self, inName):
        self.Pane('status').ResetFields()
        self.Pane('status').ResetScroll()
        self.currentStatus = inName
        self.UpdateFields()
    
    def HandleKey(self, inKey):
        currentMenu = self.menu.CurrentMenu()

        handled = currentMenu.HandleKey(inKey)

        if not handled and inKey == 'KEY_PPAGE':
            self.Pane('status').ScrollPageUp()
            handled = True
            
        if not handled and inKey == 'KEY_NPAGE':
            self.Pane('status').ScrollPageDown()
            handled = True
            
        if handled:
            self.UpdateFields()
            self.Pane('menu').Refresh()
            self.Pane('status').Refresh()
            
        return handled

    def ChangeMenu(self, inName):
        self.menu.ChangeMenu(inName)
        self.menu.CurrentMenu().HandleEnter()
    
    def Reset(self):
        self.ChangeMenu('MENU_ROOT')
        self.menu.CurrentMenu().CurrentChoiceSet(0)
        self.menu.CurrentMenu().HandleEnter()
        self.UpdateFields()
        self.Pane('menu').Refresh()
        self.Pane('status').Refresh()
            
    def AuthenticatedOnly(self, inFunc):
        if not Auth.Inst().IsAuthenticated():
            self.layout.PushDialogue(LoginDialogue(self.layout, self.parent,
                Lang('Please log in to perform this function'), inFunc))
        else:
            inFunc()
        
    def ActivateDialogue(self, inName):
        if inName == 'DIALOGUE_INTERFACE':
            self.AuthenticatedOnly(lambda: self.layout.PushDialogue(InterfaceDialogue(self.layout, self.parent)))
        elif inName == 'DIALOGUE_CHANGEPASSWORD':
            # Allow password change when not authenticated, to mitigate problems in pools
            self.layout.PushDialogue(ChangePasswordDialogue(self.layout, self.parent))
        elif inName == 'DIALOGUE_CHANGETIMEOUT':
            self.AuthenticatedOnly(lambda: self.layout.PushDialogue(ChangeTimeoutDialogue(self.layout, self.parent)))
        elif inName == 'DIALOGUE_TESTNETWORK':
            self.layout.PushDialogue(TestNetworkDialogue(self.layout,  self.parent))
        elif inName == 'DIALOGUE_DNS':
            self.AuthenticatedOnly(lambda: self.layout.PushDialogue(DNSDialogue(self.layout,  self.parent)))
        elif inName == 'DIALOGUE_HOSTNAME':
            self.AuthenticatedOnly(lambda: self.layout.PushDialogue(HostnameDialogue(self.layout,  self.parent)))
        elif inName == 'DIALOGUE_SYSLOG':
            self.AuthenticatedOnly(lambda: self.layout.PushDialogue(SyslogDialogue(self.layout,  self.parent)))
        elif inName == 'DIALOGUE_INSTALLLICENCE':
            self.AuthenticatedOnly(lambda: self.layout.PushDialogue(LicenceDialogue(self.layout,  self.parent)))
        elif inName == 'DIALOGUE_REMOTESHELL':
            self.AuthenticatedOnly(lambda: self.layout.PushDialogue(RemoteShellDialogue(self.layout,  self.parent)))
        elif inName == 'DIALOGUE_VALIDATE':
            self.layout.PushDialogue(ValidateDialogue(self.layout,  self.parent))
        elif inName == 'DIALOGUE_PATCH':
            self.AuthenticatedOnly(lambda: self.layout.PushDialogue(PatchDialogue(self.layout,  self.parent)))
        elif inName == 'DIALOGUE_BACKUP':
            self.AuthenticatedOnly(lambda: self.layout.PushDialogue(BackupDialogue(self.layout,  self.parent)))
        elif inName == 'DIALOGUE_RESTORE':
            self.AuthenticatedOnly(lambda: self.layout.PushDialogue(RestoreDialogue(self.layout,  self.parent))),
        elif inName == 'DIALOGUE_BUGREPORT':
            self.AuthenticatedOnly(lambda: self.layout.PushDialogue(QuestionDialogue(self.layout,  self.parent,
                Lang("This operation may upload sensitive data to the support server ") +
                    Config.Inst().FTPServer()+Lang(".  Do you want to continue?"), lambda x: self.BugReportDialogueHandler(x))))
        elif inName == 'DIALOGUE_SAVEBUGREPORT':
            self.AuthenticatedOnly(lambda: self.layout.PushDialogue(QuestionDialogue(self.layout,  self.parent,
                Lang("This operation may save sensitive data to removable media.  Do you want to continue?"), lambda x: self.SaveBugReportDialogueHandler(x))))
        elif inName == 'DIALOGUE_REBOOT':
            self.AuthenticatedOnly(lambda: self.layout.PushDialogue(QuestionDialogue(self.layout,  self.parent,
                Lang("Do you want to reboot this server?"), lambda x: self.RebootDialogueHandler(x))))
        elif inName == 'DIALOGUE_RECOVERY':
            self.AuthenticatedOnly(lambda: self.layout.PushDialogue(QuestionDialogue(self.layout,  self.parent,
                Lang("Do you want to reboot into Recovery Mode?"), lambda x: self.RecoveryDialogueHandler(x))))
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
            try:
                Data.Inst().RecoveryModeSet(False)
                self.layout.ExitBannerSet(Lang("Rebooting..."))
                self.layout.ExitCommandSet('/sbin/shutdown -r now')
            except Exception, e:
                self.layout.PushDialogue(InfoDialogue(self.layout, self.parent, Lang("Reboot Failed"), Lang(e)))

    def RecoveryDialogueHandler(self,  inYesNo):
        if inYesNo == 'y':
            try:
                Data.Inst().RecoveryModeSet(True)
                self.layout.ExitBannerSet(Lang("Rebooting into Recovery Mode..."))
                self.layout.ExitCommandSet('/sbin/shutdown -r now')
            except Exception, e:
                self.layout.PushDialogue(InfoDialogue(self.layout, self.parent, Lang("Reboot Failed"), Lang(e)))

    def ShutdownDialogueHandler(self,  inYesNo):
        if inYesNo == 'y':
            # Don't shutdown into recovery mode - security risk
            Data.Inst().RecoveryModeSet(False)
            self.layout.ExitBannerSet(Lang("Shutting down..."))
            self.layout.ExitCommandSet('/sbin/shutdown -h now')

    def BugReportDialogueHandler(self, inYesNo):
        if inYesNo == 'y':
            self.layout.PushDialogue(BugReportDialogue(self.layout, self.parent))

    def SaveBugReportDialogueHandler(self, inYesNo):
        if inYesNo == 'y':
            self.layout.PushDialogue(SaveBugReportDialogue(self.layout, self.parent))

    def HandleLogInOut(self):
        if Auth.Inst().IsAuthenticated():
            name = Auth.Inst().LoggedInUsername()
            Auth.Inst().LogOut()
            Data.Inst().Update()
            self.layout.PushDialogue(InfoDialogue(self.layout, self.parent, Lang("User '")+name+Lang("' logged out")))
        else:
            self.layout.PushDialogue(LoginDialogue(self.layout, self.parent))
