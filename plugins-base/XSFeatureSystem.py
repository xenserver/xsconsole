# Copyright (c) 2008-2009 Citrix Systems Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 only.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

if __name__ == "__main__":
    raise Exception("This script is a plugin for xsconsole and cannot run independently")
    
from XSConsoleStandard import *

class XSFeatureSystem:
    @classmethod
    def StatusUpdateHandlerSYSTEM(cls, inPane):
        data = Data.Inst()

        inPane.AddTitleField(Lang("System Manufacturer"))
        manufacturer = data.host.software_version.oem_manufacturer('')
        if manufacturer == '':
            manufacturer = data.dmi.system_manufacturer()
        inPane.AddWrappedTextField(manufacturer)
        inPane.NewLine()
        
        model = data.host.software_version.oem_model('')
        if model == '':
            model = data.dmi.system_product_name()
        inPane.AddTitleField(Lang("System Model"))
        inPane.AddWrappedTextField(model)
        inPane.NewLine()
        
        if Config.Inst().DisplaySerialNumber():
            inPane.AddTitleField(data.host.software_version.machine_serial_name(Lang("Serial Number")))
            serialNumber = data.host.software_version.machine_serial_number('')
            if serialNumber == '':
                serialNumber = data.dmi.system_serial_number('')
            if serialNumber == '':
                serialNumber = Lang("<Not Set>")
            inPane.AddWrappedTextField(serialNumber)
            inPane.NewLine()
        
        if Config.Inst().DisplayAssetTag():
            inPane.AddTitleField(Lang("Asset Tag"))
            assetTag = data.dmi.asset_tag('') # FIXME: Get from XAPI when available
            if assetTag == '':
                assetTag = Lang("<Not Set>")
            inPane.AddWrappedTextField(assetTag) 

        inPane.AddKeyHelpField( { Lang("<F5>") : Lang("Refresh")})

    @classmethod
    def StatusUpdateHandlerPROCESSOR(cls, inPane):
        data = Data.Inst()

        inPane.AddTitleField(Lang("Processor Details"))
        
        inPane.AddStatusField(Lang("Logical CPUs", 27), str(len(data.host.host_CPUs([]))))
        inPane.AddStatusField(Lang("Populated CPU Sockets", 27), str(data.dmi.cpu_populated_sockets()))
        inPane.AddStatusField(Lang("Total CPU Sockets", 27), str(data.dmi.cpu_sockets()))

        inPane.NewLine()
        inPane.AddTitleField(Lang("Description"))
        
        for name, value in data.derived.cpu_name_summary().iteritems():
            # Use DMI number for populated sockets, not xapi-reported number of logical cores 
            inPane.AddWrappedTextField(str(data.dmi.cpu_populated_sockets())+" x "+name)
            
            # inPane.AddWrappedTextField(str(value)+" x "+name) # Alternative - number of logical cores
    
        inPane.AddKeyHelpField( { Lang("<F5>") : Lang("Refresh")})
    
    @classmethod
    def StatusUpdateHandlerMEMORY(cls, inPane):
        data = Data.Inst()
        
        inPane.AddTitleField(Lang("System Memory"))
        
        xapiMemory = int(data.host.metrics.memory_total(0)) /  1048576 # Convert from bytes to MB
        dmiMemory = data.dmi.memory_size(0)
        
        if xapiMemory != 0 and (dmiMemory < xapiMemory * 0.9 or dmiMemory > xapiMemory * 1.1):
            # DMI memory doesn't agree with xapi, probably due to errors in the
            # BIOS DMI information.  Prefer xapi's value
            inPane.AddStatusField(Lang("Total memory", 26), str(int(xapiMemory))+' MB')
            XSLog('xapi total memory ('+str(int(xapiMemory))+" MB) doesn't match DMI total memory ("+str(int(dmiMemory))+' MB)')
            # Don't display possibly invalid socket information
        else:
            inPane.AddStatusField(Lang("Total memory", 26), str(int(dmiMemory))+' MB')
            inPane.AddStatusField(Lang("Populated memory sockets", 26), str(data.dmi.memory_modules()))
            inPane.AddStatusField(Lang("Total memory sockets", 26), str(data.dmi.memory_sockets()))

        inPane.AddKeyHelpField( { Lang("<F5>") : Lang("Refresh")})

    @classmethod
    def StatusUpdateHandlerSTORAGE(cls, inPane):
        data = Data.Inst()
        
        inPane.AddTitleField(Lang("Local Storage Controllers"))
        
        for devClass, name in data.lspci.storage_controllers([]):
            inPane.AddWrappedBoldTextField(devClass)
            inPane.AddWrappedTextField(name)
            inPane.NewLine()
    
        inPane.AddKeyHelpField( { Lang("<F5>") : Lang("Refresh")})

    @classmethod
    def StatusUpdateHandlerBMC(cls, inPane):
        data = Data.Inst()
        
        inPane.AddTitleField(Lang(Config.Inst().BMCName()+" Information"))
        
        inPane.AddStatusField(Lang(Config.Inst().BMCName()+" Firmware Version",  22), data.bmc.version())
        
        inPane.AddKeyHelpField( { Lang("<F5>") : Lang("Refresh")})

    @classmethod
    def StatusUpdateHandlerBIOS(cls, inPane):
        data = Data.Inst()
        
        inPane.AddTitleField(Lang("BIOS Information"))
        
        inPane.AddStatusField(Lang("Vendor", 12), data.dmi.bios_vendor())
        inPane.AddStatusField(Lang("Version", 12), data.dmi.bios_version())

        inPane.AddKeyHelpField( { Lang("<F5>") : Lang("Refresh")})
        
    def Register(self):
        
        Importer.RegisterNamedPlugIn(
            self,
            'SYSTEM_DESCRIPTION', # Key of this plugin for replacement, etc.
            {
                'title' : Lang('System Description'), # Name of this plugin for plugin list
                'menuname' : 'MENU_PROPERTIES',
                'menupriority' : 100,
                'menutext' : Lang('System Description') ,
                'statusupdatehandler' : self.StatusUpdateHandlerSYSTEM
            }
        )

        Importer.RegisterNamedPlugIn(
            self,
            'PROCESSOR', # Key of this plugin for replacement, etc.
            {
                'title' : Lang('Processor'), # Name of this plugin for plugin list
                'menuname' : 'MENU_PROPERTIES',
                'menupriority' : 200,
                'menutext' : Lang('Processor') ,
                'statusupdatehandler' : self.StatusUpdateHandlerPROCESSOR
            }
        )
            
        Importer.RegisterNamedPlugIn(
            self,
            'MEMORY', # Key of this plugin for replacement, etc.
            {
                'title' : Lang('System Memory'), # Name of this plugin for plugin list
                'menuname' : 'MENU_PROPERTIES',
                'menupriority' : 300,
                'menutext' : Lang('System Memory') ,
                'statusupdatehandler' : self.StatusUpdateHandlerMEMORY
            }
        )
        
        Importer.RegisterNamedPlugIn(
            self,
            'LOCAL_STORAGE_CONTROLLERS', # Key of this plugin for replacement, etc.
            {
                'title' : Lang('Local Storage Controllers'), # Name of this plugin for plugin list
                'menuname' : 'MENU_PROPERTIES',
                'menupriority' : 400,
                'menutext' : Lang('Local Storage Controllers') ,
                'statusupdatehandler' : self.StatusUpdateHandlerSTORAGE
            }
        )
            
        Importer.RegisterNamedPlugIn(
            self,
            'BIOS', # Key of this plugin for replacement, etc.
            {
                'title' : Lang('BIOS Information'), # Name of this plugin for plugin list
                'menuname' : 'MENU_PROPERTIES',
                'menupriority' : 500,
                'menutext' : Lang('BIOS Information') ,
                'statusupdatehandler' : self.StatusUpdateHandlerBIOS
            }
        )
        
        if Data.Inst().bmc.version('') != '':
            Importer.RegisterNamedPlugIn(
                self,
                'BMC', # Key of this plugin for replacement, etc.
                {
                    'menuname' : 'MENU_PROPERTIES',
                    'menupriority' : 600,
                    'menutext' : Lang(Config.Inst().BMCName()+' Version'),
                    'statusupdatehandler' : self.StatusUpdateHandlerBMC
                }
            )
            

# Register this plugin when module is imported
XSFeatureSystem().Register()
