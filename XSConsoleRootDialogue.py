# Copyright (c) Citrix Systems 2007. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

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
        menuPane = self.NewPane(DialoguePane(self.parent, PaneSizerFixed(1, 2, 39, 21)), 'menu')
        menuPane.ColoursSet('MENU_BASE', 'MENU_BRIGHT', 'MENU_HIGHLIGHT')
        statusPane = self.NewPane(DialoguePane(self.parent, PaneSizerFixed(40, 2, 39, 21)), 'status')
        statusPane.ColoursSet('HELP_BASE', 'HELP_BRIGHT')
        self.menu = RootMenu(self)
        self.currentStatus = 'STATUS'
        self.UpdateFields()

    def UpdateFieldsSTATUS(self, inPane):
        data = Data.Inst()

        inPane.AddWrappedTextField(data.dmi.system_manufacturer())
        inPane.AddWrappedTextField(data.dmi.system_product_name())
        inPane.NewLine()
        inPane.AddWrappedTextField(Language.Inst().Branding(data.host.software_version.product_brand()) + ' ' +
            data.derived.fullversion())
        inPane.NewLine()
        inPane.AddTitleField(Lang("Management Network Parameters"))
        
        if len(data.derived.managementpifs([])) == 0:
            inPane.AddWrappedTextField(Lang("<No network configured>"))
        else:
            inPane.AddStatusField(Lang('Device', 16), data.derived.managementpifs()[0]['device'])
            inPane.AddStatusField(Lang('IP address', 16), data.ManagementIP(''))
            inPane.AddStatusField(Lang('Netmask', 16),  data.ManagementNetmask(''))
            inPane.AddStatusField(Lang('Gateway', 16),  data.ManagementGateway(''))
    
        inPane.AddKeyHelpField( { Lang("<F5>") : Lang("Refresh")})
        
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
            inPane.AddWrappedTextField(Lang("You are logged in."))
        else:
            inPane.AddWrappedTextField(Lang("You are currently not logged in."))

        inPane.NewLine()
        inPane.AddWrappedTextField(Lang("Only logged in users can reconfigure and control this server."))
        
        inPane.AddKeyHelpField( { Lang("<F5>") : Lang("Refresh")})

    def UpdateFieldsLOGINOUT(self, inPane):
        if Auth.Inst().IsAuthenticated():
            inPane.AddTitleField(Lang("Log Out"))
            inPane.AddWrappedTextField(Lang("Press <Enter> to log out."))
            inPane.AddKeyHelpField( {Lang("<Enter>") : Lang("Log out") })
        else:
            inPane.AddTitleField(Lang("Log In"))
            inPane.AddWrappedTextField(Lang("Press <Enter> to log in."))
            inPane.AddKeyHelpField( { Lang("<Enter>") : Lang("Log in") })

    def UpdateFieldsCHANGEPASSWORD(self, inPane):
        inPane.AddTitleField(Lang("Change Password"))
    
        inPane.AddWrappedTextField(Lang("Press <Enter> to change the password for user 'root'.  "
        "This will also change the password for local and remote login shells.  "
        "If this host is in a pool, it will also change the password of the pool master."))
        
        inPane.AddKeyHelpField( { Lang("<Enter>") : Lang("Change Password") })

    def UpdateFieldsCHANGETIMEOUT(self, inPane):
        inPane.AddTitleField(Lang("Change Auto-Logout Time"))
    
        timeout = State.Inst().AuthTimeoutMinutes()
        message = Lang("The current auto-logout time is ") + str(timeout) + " "

        message += Language.Quantity("minute", timeout) + ".  "
        message += Lang("Users will be automatically logged out after there has been no keyboard "
            "activity for this time.  This timeout applies to this console and to "
            "local shells started from this console.")
    
        inPane.AddWrappedTextField(message)
        
        inPane.AddKeyHelpField( { Lang("<Enter>") : Lang("Change Timeout") })

    def UpdateFieldsINTERFACE(self, inPane):
        inPane.AddTitleField(Lang("Server Management"))
    
        inPane.AddWrappedTextField(Lang(
            "This menu configures general server operation, including the management network, "
            "hostname, remote logging (syslog), licensing, and local storage repositories."))
        
    def UpdateFieldsXENSERVER(self, inPane):
        data = Data.Inst()

        inPane.AddTitleField(Lang("XenServer Product Information"))
        inPane.AddStatusField(Lang("Name", 16), Language.Inst().Branding((data.host.software_version.product_brand())))
        inPane.AddStatusField(Lang("Version", 16), str(data.derived.fullversion()))
        inPane.AddStatusField(Lang("Xen Version", 16), str(data.host.software_version.xen()))
        inPane.AddStatusField(Lang("Kernel Version",16), str(data.host.software_version.linux()))
    
        inPane.AddKeyHelpField( { Lang("<F5>") : Lang("Refresh")})

    def UpdateFieldsLICENCE(self, inPane):
        data = Data.Inst()

        expiryStr = data.host.license_params.expiry()
        if (re.match('\d{8}', expiryStr)):
            # Convert ISO date to more readable form
            expiryStr = expiryStr[0:4]+'-'+expiryStr[4:6]+'-'+expiryStr[6:8]
        
        inPane.AddTitleField(Lang("License"))
        inPane.AddStatusField(Lang("Product SKU", 16), str(Language.Inst().Branding(data.host.license_params.sku_type())))
        inPane.AddStatusField(Lang("Expiry", 16), expiryStr)
        inPane.AddStatusField(Lang("Sockets", 16), str(data.host.license_params.sockets()))
        inPane.NewLine()
        inPane.AddTitleField(Lang("Product Code"))
        inPane.AddWrappedTextField(str(data.host.license_params.productcode()))
        inPane.NewLine()
        inPane.AddTitleField(Lang("Serial Number"))
        inPane.AddWrappedTextField(str(data.host.license_params.serialnumber()))

        inPane.AddKeyHelpField( { Lang("<F5>") : Lang("Refresh")})

    def UpdateFieldsHOST(self, inPane):
        data = Data.Inst()

        inPane.AddTitleField(Lang("Hostname"))
        inPane.AddWrappedTextField(data.host.name_label())
        
        inPane.AddKeyHelpField( { Lang("<F5>") : Lang("Refresh")})

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

        inPane.AddKeyHelpField( { Lang("<F5>") : Lang("Refresh")})

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
    
        inPane.AddKeyHelpField( { Lang("<F5>") : Lang("Refresh")})
    
    def UpdateFieldsMEMORY(self, inPane):
        data = Data.Inst()
        
        inPane.AddTitleField(Lang("System Memory"))
            
        inPane.AddStatusField(Lang("Total memory", 27), str(data.dmi.memory_size())+' MB')
        inPane.AddStatusField(Lang("Populated memory sockets", 27), str(data.dmi.memory_modules()))
        inPane.AddStatusField(Lang("Total memory sockets", 27), str(data.dmi.memory_sockets()))

        inPane.AddKeyHelpField( { Lang("<F5>") : Lang("Refresh")})

    def UpdateFieldsSTORAGE(self, inPane):
        data = Data.Inst()
        
        inPane.AddTitleField(Lang("Local Storage Controllers"))
        
        for name in data.lspci.storage_controllers([]):
            inPane.AddWrappedTextField(name)
            inPane.NewLine()
    
        inPane.AddKeyHelpField( { Lang("<F5>") : Lang("Refresh")})

    def UpdateFieldsPIF(self, inPane):
        data = Data.Inst()
        
        inPane.AddTitleField(Lang("Network Interfaces"))
        
        for pif in data.host.PIFs([]):
            inPane.AddWrappedBoldTextField(pif['metrics']['device_name'])
            if pif['metrics']['carrier']:
                inPane.AddWrappedTextField(Lang("(connected)"))
            else:
                inPane.AddWrappedTextField(Lang("(not connected)"))
                
            inPane.AddStatusField(Lang("MAC Address", 16), pif['MAC'])
            inPane.AddStatusField(Lang("Device", 16), pif['device'])
            inPane.NewLine()

    def UpdateFieldsBMC(self, inPane):
        data = Data.Inst()
        
        inPane.AddTitleField(Lang("BMC Information"))
        
        inPane.AddStatusField(Lang("BMC Firmware Version",  22), data.bmc.version())
        
        inPane.AddKeyHelpField( { Lang("<F5>") : Lang("Refresh")})

    def UpdateFieldsCPLD(self, inPane):
        data = Data.Inst()
        
        inPane.AddTitleField(Lang("CPLD Information"))

        inPane.AddWrappedTextField(Lang("Not available"))

    def UpdateFieldsBIOS(self, inPane):
        data = Data.Inst()
        
        inPane.AddTitleField(Lang("BIOS Information"))
        
        inPane.AddStatusField(Lang("Vendor", 12), data.dmi.bios_vendor())
        inPane.AddStatusField(Lang("Version", 12), data.dmi.bios_version())

        inPane.AddKeyHelpField( { Lang("<F5>") : Lang("Refresh")})

    def UpdateFieldsSELECTNIC(self, inPane):
        data = Data.Inst()
        
        inPane.AddTitleField(Lang("Current Management Interface"))
        
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
        })
        
    def UpdateFieldsTESTNETWORK(self, inPane):
        inPane.AddTitleField(Lang("Test Network"))
    
        inPane.AddWrappedTextField(Lang(
            "This option will test the configured network using ping."))
        
        inPane.AddKeyHelpField( { Lang("<Enter>") : Lang("Test Network") })
        
    def UpdateFieldsREBOOTSHUTDOWN(self, inPane):
        inPane.AddTitleField(Lang("Reboot/Shutdown"))
    
        inPane.AddWrappedTextField(Lang(
            "This option can reboot or shutdown this server."))
    
    def UpdateFieldsREBOOT(self, inPane):
        inPane.AddTitleField(Lang("Reboot Server"))
    
        inPane.AddWrappedTextField(Lang(
            "Press <Enter> to reboot this server into normal operating mode."))
    
        inPane.AddKeyHelpField( {
            Lang("<Enter>") : Lang("Reboot Server")
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
            "Press <Enter> to start a local command shell on this server.  "
            "This shell will have root privileges."))
 
    def UpdateFieldsQUIT(self, inPane):
        inPane.AddTitleField(Lang("Quit"))
    
        inPane.AddWrappedTextField(Lang(
            "Press <Enter> to quit this console."))
 
    def UpdateFieldsBURP(self, inPane):
        inPane.AddTitleField(Lang("Backup, Restore and Update"))
    
        inPane.AddWrappedTextField(Lang(
            "From this menu you can backup and restore the system database, and apply "
            "software updates or patches to the system."))
        
    def UpdateFieldsTECHNICAL(self, inPane):
        inPane.AddTitleField(Lang("Technical Support"))
    
        inPane.AddWrappedTextField(Lang(
            "From this menu you can enable remote shells (ssh), "
            "validate the configuration of this server and upload or save bug reports."))
    
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

        inPane.AddWrappedTextField(Lang(
            "Press <Enter> to apply a software upgrade or patch."))
        inPane.AddKeyHelpField( { Lang("<Enter>") : Lang("Upgrade or Patch") } )   
 
    def UpdateFieldsBACKUP(self, inPane):
        data = Data.Inst()
        inPane.AddTitleField(Lang("Backup Server State"))

        inPane.AddWrappedTextField(Lang(
            "Press <Enter> to backup the server state to removable media."))
            
        inPane.AddKeyHelpField( { Lang("<Enter>") : Lang("Backup") } ) 
 
    def UpdateFieldsRESTORE(self, inPane):
        data = Data.Inst()
        inPane.AddTitleField(Lang("Restore Server State"))

        inPane.AddWrappedTextField(Lang(
            "Press <Enter> to restore the server state from removable media."))
        inPane.AddKeyHelpField( { Lang("<Enter>") : Lang("Restore") } ) 
 
    def UpdateFieldsREVERT(self, inPane):
        data = Data.Inst()
        inPane.AddTitleField(Lang("Revert to a Pre-Patch Version"))

        inPane.AddWrappedTextField(Lang(
            "Press <Enter> to revert to a version prior to an applied patch."))
        inPane.NewLine()
        
        inPane.AddStatusField(Lang('Current Label', 16), data.backup.currentlabel(''))
        inPane.AddStatusField(Lang('Previous Label', 16), data.backup.previouslabel(''))
            
        inPane.AddKeyHelpField( { Lang("<Enter>") : Lang("Revert") } ) 
 
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
        
    def UpdateFieldsVERBOSEBOOT(self, inPane):
        data = Data.Inst()
        inPane.AddTitleField(Lang("Enable/Disable Verbose Boot Mode"))

        if State.Inst().VerboseBoot() is None:
            message = Lang('unknown.  To enable or disable')
        elif State.Inst().VerboseBoot():
            message = Lang('enabled.  To disable')
        else:
            message = Lang('disabled.  To enable')

        inPane.AddWrappedTextField(Lang(
            "This option will control the level of information displayed as this server boots.  "
            "The current state of verbose boot mode is ")+message+Lang(" press <Enter>."))
            
        inPane.AddKeyHelpField( { Lang("<Enter>") : Lang("Configure") } )  
    
    def UpdateFieldsRESET(self, inPane):
        data = Data.Inst()
        inPane.AddTitleField(Lang("Reset to Factory Defaults"))

        inPane.AddWrappedTextField(Lang(
            "This option will reset all configuration information to default values, "
            "delete all virtual machines and delete all storage repositories on local disks."))
            
        inPane.AddKeyHelpField( { Lang("<Enter>") : Lang("Reset") } )  
    
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
                                        "interfaces are configured to use DHCP."))
        inPane.AddKeyHelpField( {
            Lang("<Enter>") : Lang("Reconfigure DNS"),
            Lang("<F5>") : Lang("Refresh")
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
            Lang("<Enter>") : Lang("Set Hostname"),
            Lang("<F5>") : Lang("Refresh")
        })

    def UpdateFieldsSR(self, inPane):
        data = Data.Inst()
        inPane.AddTitleField(Lang("Disks and Storage Repositories"))
    
        inPane.AddWrappedTextField(Lang("Local disks can be configured as storage repositories "
            "for use by virtual machines.  Press <Enter> to list the disks available."))

        inPane.AddKeyHelpField( {
            Lang("<Enter>") : Lang("Configure SRs")
        })

    def UpdateFieldsREMOTE(self, inPane):
        data = Data.Inst()
        inPane.AddTitleField(Lang("Remote Resource Configuration"))
    
        inPane.AddWrappedTextField(Lang("This menu configures Storage Repositories for suspend images and crash dumps, and remote databases."))

    def UpdateFieldsREMOTEDB(self, inPane):
        data = Data.Inst()
        inPane.AddTitleField(Lang("Setup Remote Database"))
    
        if not data.remotedb.is_on_remote_storage(False):
            inPane.AddWrappedTextField(Lang("A remote database is not configured on this server."))
        else:
            inPane.AddWrappedTextField(Lang("A remote database is configured for this server on an iSCSI LUN."))
            inPane.NewLine()
            inPane.AddStatusField(Lang('Server', 10), data.remotedb.target()+":"+data.remotedb.port())
            inPane.AddStatusField(Lang('LUN',10), data.remotedb.lun())
            if data.remotedb.username('') != '':
                inPane.AddStatusField(Lang('Username', 10), data.remotedb.username())
            inPane.NewLine()
            inPane.AddTitleField(Lang("Initiator IQN"))
            inPane.AddWrappedTextField(data.remotedb.localiqn())
            inPane.NewLine()
            inPane.AddTitleField(Lang("Target IQN"))
            inPane.AddWrappedTextField(data.remotedb.remoteiqn())

        inPane.AddKeyHelpField( {
            Lang("<Enter>") : Lang("Configure Remote DB")
        })

    def UpdateFieldsSUSPENDSR(self, inPane):
        data = Data.Inst()
        inPane.AddTitleField(Lang("Specify Suspend SR"))
    
        inPane.AddWrappedTextField(Lang("This server can be configured to use a Storage Repository for suspend images."))
        inPane.NewLine()
    
        if not data.host.suspend_image_sr(False):
            inPane.AddWrappedTextField(Lang("A Suspend Image SR is not configured on this server."))
        else:
            inPane.AddWrappedTextField(Lang("The SR named '")+data.host.suspend_image_sr.name_label()+Lang("' is configured as the Suspend Image SR for this server."))
            
        inPane.AddKeyHelpField( {
            Lang("<Enter>") : Lang("Specify Suspend SR")
        })

    def UpdateFieldsCRASHDUMPSR(self, inPane):
        data = Data.Inst()
        inPane.AddTitleField(Lang("Specify Crash Dump SR"))
    
        inPane.AddWrappedTextField(Lang("This server can be configured to use Storage Repository to store Crash Dumps."))
        inPane.NewLine()
    
        if not data.host.crash_dump_sr(False):
            inPane.AddWrappedTextField(Lang("A Crash Dump SR is not configured on this server."))
        else:
            inPane.AddWrappedTextField(Lang("The SR named '")+data.host.crash_dump_sr.name_label()+Lang("' is configured as the Crash Dump SR for this server."))
            
        inPane.AddKeyHelpField( {
            Lang("<Enter>") : Lang("Specify Crash Dump SR")
        })

    def UpdateFieldsSYSLOG(self, inPane):
        data = Data.Inst()
        inPane.AddTitleField(Lang("Remote Logging (syslog)"))
    
        if data.host.logging.syslog_destination('') == '':
            inPane.AddWrappedTextField(Lang("Remote logging is not configured on this host.  Press <Enter> to activate and set a destination address."))
        else:
            inPane.AddWrappedTextField(Lang("The remote logging destination for this host is"))
            inPane.NewLine()
            inPane.AddWrappedTextField(data.host.logging.syslog_destination())
        
        inPane.AddKeyHelpField( {
            Lang("<Enter>") : Lang("Reconfigure"),
            Lang("<F5>") : Lang("Refresh")
        })

    def UpdateFieldsNTP(self, inPane):
        data = Data.Inst()
        inPane.AddTitleField(Lang("Network Time (NTP)"))
        
        inPane.AddWrappedTextField(Lang("One or more network time servers can be configured to synchronize time between servers.  This is especially important for pooled servers."))
        inPane.NewLine()
        
        if not data.chkconfig.ntpd(False):
            inPane.AddWrappedTextField(Lang("Currently NTP is disabled, and the following servers are configured."))
        else:
            inPane.AddWrappedTextField(Lang("Currently NTP is enabled, and the following servers are configured."))
        
        inPane.NewLine()
        
        servers = data.ntp.servers([])        
        if len(servers) == 0:
            inPane.AddWrappedTextField(Lang("<No servers configured>"))
        else:
            for server in servers:
                inPane.AddWrappedTextField(server)
        
        inPane.AddKeyHelpField( {
            Lang("<Enter>") : Lang("Reconfigure"),
            Lang("<F5>") : Lang("Refresh")
        })

    def UpdateFieldsTIMEZONE(self, inPane):
        data = Data.Inst()
        inPane.AddTitleField(Lang("Set Timezone"))
        
        inPane.AddWrappedTextField(Lang("Use this option to set the timezone for this server."))
        inPane.NewLine()
        if data.timezones.current('') != '':
            inPane.AddWrappedTextField(Lang("The current timezone is"))
            inPane.NewLine()
            inPane.AddWrappedTextField(data.timezones.current(Lang('<Unknown>')))
            inPane.NewLine()

    def UpdateFieldsKEYBOARD(self, inPane):
        data = Data.Inst()
        inPane.AddTitleField(Lang("Keyboard Language and Layout"))
        
        inPane.AddWrappedTextField(Lang("Use this option to select the correct language and layout for your keyboard."))
        inPane.NewLine()
        if data.keyboard.currentname('') != '':
            inPane.AddWrappedTextField(Lang("The current keyboard type is"))
            inPane.NewLine()
            inPane.AddWrappedTextField(data.keyboard.currentname(Lang('<Unknown>')))
            inPane.NewLine()
            
    def UpdateFieldsEXCEPTION(self, inPane,  inException):
        inPane.AddTitleField(Lang("Information not available"))
        inPane.AddWrappedTextField(Lang("You may need to log in to view this information"))
        inPane.AddWrappedTextField(str(inException))

    def UpdateFields(self):
        menuPane = self.Pane('menu')
        menuPane.ResetFields()
        menuPane.ResetPosition()
        menuPane.AddTitleField(self.menu.CurrentMenu().Title())
        # Scrolling doesn't work well for this menu because it's recreated on update.  Preserving the
        # scroll position would improve it if there are more than 15 entries
        menuPane.AddMenuField(self.menu.CurrentMenu(), 15) # Allow extra height for this menu
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
        
        if statusPane.NumStaticFields() == 0: # No key help yet
            if statusPane.NeedsScroll():
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
        self.menu.Reset()
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
        elif inName == 'DIALOGUE_NTP':
            self.AuthenticatedOnly(lambda: self.layout.PushDialogue(NTPDialogue(self.layout,  self.parent)))
        elif inName == 'DIALOGUE_TIMEZONE':
            self.AuthenticatedOnly(lambda: self.layout.PushDialogue(TimezoneDialogue(self.layout,  self.parent)))
        elif inName == 'DIALOGUE_KEYBOARD':
            self.layout.PushDialogue(KeyboardDialogue(self.layout,  self.parent))
        elif inName == 'DIALOGUE_SR':
            self.AuthenticatedOnly(lambda: self.layout.PushDialogue(ClaimSRDialogue(self.layout,  self.parent)))
        elif inName == 'DIALOGUE_REMOTEDB':
            self.AuthenticatedOnly(lambda: self.layout.PushDialogue(RemoteDBDialogue(self.layout,  self.parent)))
        elif inName == 'DIALOGUE_SUSPENDSR':
            self.AuthenticatedOnly(lambda: self.layout.PushDialogue(SuspendSRDialogue(self.layout,  self.parent)))
        elif inName == 'DIALOGUE_CRASHDUMPSR':
            self.AuthenticatedOnly(lambda: self.layout.PushDialogue(CrashDumpSRDialogue(self.layout,  self.parent)))
        elif inName == 'DIALOGUE_INSTALLLICENCE':
            self.AuthenticatedOnly(lambda: self.layout.PushDialogue(LicenceDialogue(self.layout,  self.parent)))
        elif inName == 'DIALOGUE_REMOTESHELL':
            self.AuthenticatedOnly(lambda: self.layout.PushDialogue(RemoteShellDialogue(self.layout,  self.parent)))
        elif inName == 'DIALOGUE_VALIDATE':
            self.layout.PushDialogue(ValidateDialogue(self.layout,  self.parent))
        elif inName == 'DIALOGUE_VERBOSEBOOT':
            self.AuthenticatedOnly(lambda: self.layout.PushDialogue(VerboseBootDialogue(self.layout, self.parent)))
        elif inName == 'DIALOGUE_RESET':
            self.AuthenticatedOnly(lambda: self.layout.PushDialogue(ResetDialogue(self.layout, self.parent)))
        elif inName == 'DIALOGUE_PATCH':
            self.AuthenticatedOnly(lambda: self.layout.PushDialogue(PatchDialogue(self.layout,  self.parent)))
        elif inName == 'DIALOGUE_BACKUP':
            self.AuthenticatedOnly(lambda: self.layout.PushDialogue(BackupDialogue(self.layout,  self.parent)))
        elif inName == 'DIALOGUE_RESTORE':
            self.AuthenticatedOnly(lambda: self.layout.PushDialogue(RestoreDialogue(self.layout,  self.parent))),
        elif inName == 'DIALOGUE_REVERT':
            self.AuthenticatedOnly(lambda: self.layout.PushDialogue(QuestionDialogue(self.layout,  self.parent,
                Lang("Do you want to revert this patch?"), lambda x: self.RevertDialogueHandler(x))))
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
        elif inName == 'DIALOGUE_SHUTDOWN':
            self.AuthenticatedOnly(lambda: self.layout.PushDialogue(QuestionDialogue(self.layout,  self.parent,
                Lang("Do you want to shutdown this server?"), lambda x: self.ShutdownDialogueHandler(x))))
        elif inName == 'DIALOGUE_LOCALSHELL':
            self.AuthenticatedOnly(lambda: self.StartLocalShell())
        elif inName == 'DIALOGUE_QUIT':
                self.layout.ExitBannerSet(Lang("Quitting..."))
                self.layout.ExitCommandSet('') # Just exit
            
    def StartLocalShell(self):
        user = os.environ.get('USER', 'root')
        self.layout.ExitBannerSet(Lang("\rShell for local user '")+user+"'.\r\r"+
                Lang("Type 'exit' to return to the management console.\r"))
        self.layout.SubshellCommandSet("( export TMOUT="+str(State.Inst().AuthTimeoutSeconds())+" && /bin/bash --login )")
            
    def RebootDialogueHandler(self,  inYesNo):
        if inYesNo == 'y':
            try:
                self.layout.ExitBannerSet(Lang("Rebooting..."))
                self.layout.ExitCommandSet('/sbin/shutdown -r now')
            except Exception, e:
                self.layout.PushDialogue(InfoDialogue(self.layout, self.parent, Lang("Reboot Failed"), Lang(e)))

    def ShutdownDialogueHandler(self,  inYesNo):
        if inYesNo == 'y':
            self.layout.ExitBannerSet(Lang("Shutting down..."))
            self.layout.ExitCommandSet('/sbin/shutdown -h now')

    def RevertDialogueHandler(self, inYesNo):
        if inYesNo == 'y':
            try:
                Data.Inst().Revert()
                self.layout.PushDialogue(QuestionDialogue(
                    self.layout, self.parent,
                    Lang("To use the reverted version you need to reboot.  Would you like to reboot now?"),
                    lambda x: self.layout.TopDialogue().RebootDialogueHandler(x)
                ))
            except Exception, e:
                self.layout.PushDialogue(InfoDialogue(self.layout, self.parent, Lang("Revert Failed"), Lang(e)))

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
