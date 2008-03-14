# Copyright (c) Citrix Systems 2008. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

if __name__ == "__main__":
    raise Exception("This script is a plugin for xsconsole and cannot run independently")
    
from XSConsoleStandard import *
from XSConsolePlugIn import *

class InstallLicenceDialogue(FileDialogue):
    def __init__(self):

        self.custom = {
            'title' : Lang("Install License"),
            'searchregexp' : r'.*licen[cs]e',  # Licence files always contain the string licence or license
            'deviceprompt' : Lang("Select The Device Containing The License File"), 
            'fileprompt' : Lang("Select The License File"),
            'confirmprompt' : Lang("Press <F8> To Install The License"),
            'mode' : 'ro'
        }
        FileDialogue.__init__(self) # Must fill in self.custom before calling __init__
        
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

class XSFeatureInstallLicence(PlugIn):
    def __init__(self):
        PlugIn.__init__(self)
        
    @classmethod
    def StatusUpdateHandler(cls, inPane):
        data = Data.Inst()
        inPane.AddTitleField(Lang("Install License File"))

        data = Data.Inst()

        expiryStr = data.host.license_params.expiry()
        if (re.match('\d{8}', expiryStr)):
            # Convert ISO date to more readable form
            expiryStr = expiryStr[0:4]+'-'+expiryStr[4:6]+'-'+expiryStr[6:8]
        
                
        inPane.AddWrappedTextField(Lang(
            "Press <Enter> to install a license file from removable media."))
        inPane.NewLine()
        inPane.AddTitleField(Lang("Current License"))
        inPane.AddStatusField(Lang("Product SKU", 16), data.host.license_params.sku_marketing_name())
        inPane.AddStatusField(Lang("Expiry", 16), expiryStr)
        inPane.AddStatusField(Lang("Sockets", 16), str(data.host.license_params.sockets()))
        inPane.NewLine()
        inPane.AddWrappedBoldTextField(Lang("Product Code"))
        inPane.AddWrappedTextField(str(data.host.license_params.productcode()))
        inPane.NewLine()
        inPane.AddWrappedBoldTextField(Lang("Serial Number"))
        inPane.AddWrappedTextField(str(data.host.license_params.serialnumber()))
 
        inPane.AddKeyHelpField( {
            Lang("<Enter>") : Lang("Install License")
        } )
        
    @classmethod
    def ActivateHandler(cls):
        DialogueUtils.AuthenticatedOnly(lambda: Layout.Inst().PushDialogue(InstallLicenceDialogue()))
        
    def Register(self):
        data = Data.Inst()
        Importer.RegisterNamedPlugIn(
            self,
            'INSTALL_LICENCE', # Key of this plugin for replacement, etc.
            {
                'title' : Lang('Install XenServer License'), # Name of this plugin for plugin list
                'menuname' : 'MENU_XENDETAILS',
                'menupriority' : 100,
                'menutext' : Lang('Install XenServer License') ,
                'statusupdatehandler' : self.StatusUpdateHandler,
                'activatehandler' : self.ActivateHandler
            }
        )

# Register this plugin when module is imported
XSFeatureInstallLicence().Register()
