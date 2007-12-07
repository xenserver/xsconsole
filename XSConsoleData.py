# Copyright (c) Citrix Systems 2007. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

import XenAPI

import commands, re, sys, tempfile
from pprint import pprint

from XSConsoleAuth import *
from XSConsoleLang import *
from XSConsoleState import *
from XSConsoleUtils import *

class DataMethod:
    def __init__(self, inSend, inName):
        self.send = inSend
        self.name = inName
        
    def __getattr__(self, inName):
        return DataMethod(self.send, self.name+[inName])

    def __call__(self,  inDefault = None):
        return self.send(self.name,  inDefault)

class Data:
    instance = None
    
    def __init__(self):
        self.data = {}
        self.session = None
    
    @classmethod
    def Inst(cls):
        if cls.instance is None:
            cls.instance = Data()
            cls.instance.Create()
        return cls.instance
    
    @classmethod
    def Reset(cls):
        if cls.instance is not None:
            del cls.instance
            cls.instance = None
            
    def GetData(self, inNames, inDefault = None):
        data = self.data
        for name in inNames:
            if name is '__repr__':
                # Error - missing ()
                raise Exception('Data call Data.' + '.'.join(inNames[:-1]) + ' must end with ()')
            elif name in data:
                data = data[name]
            else:
                return FirstValue(inDefault, Lang('<Unknown>'))
        return data
    
    # Attribute access can be used in two ways
    #   self.host.software_version.oem_model()
    # returns the value of self.data['host']['software_version']['oem_model'], or the string '<Unknown>'
    # if the element doesn't exist.
    #   self.host.software_version.oem_model('Default')
    # is similar but returns the parameter ('Default' in this case) if the element doesn't exist
    def __getattr__(self, inName):
        if inName[0].isupper():
            # Don't expect elements to start with upper case, so probably an unknown method name
            raise Exception("Unknown method Data."+inName)
        return DataMethod(self.GetData, [inName])
    
    def RequireSession(self):
        if self.session is None: self.session = Auth.Inst().OpenSession()
    
    def Create(self):
        # Create fills in data that never changes.  Update fills volatile data
        self.data = {}
        
        (status, output) = commands.getstatusoutput("dmidecode")
        if status != 0:
            # Use test dmidecode file if there's no real output
            (status, output) = commands.getstatusoutput("/bin/cat ./dmidecode.txt")
        
        if status == 0:
            self.ScanDmiDecode(output.split("\n"))
     
        (status, output) = commands.getstatusoutput("/sbin/lspci")
        if status != 0:
            (status, output) = commands.getstatusoutput("/usr/bin/lspci")

        if status == 0:
            self.ScanLspci(output.split("\n"))
     
        if os.path.isfile("/usr/bin/ipmitool"):
            (status, output) = commands.getstatusoutput("/usr/bin/ipmitool mc info")
            if status == 0:
                self.ScanIpmiMcInfo(output.split("\n"))
        
        # /proc/cpuinfo has details of the virtual CPUs exposed to DOM-0, not necessarily the real CPUs
        (status, output) = commands.getstatusoutput("/bin/cat /proc/cpuinfo")
        if status == 0:
            self.ScanCPUInfo(output.split("\n"))
        
        self.Update()
    
    def Update(self):
        self.data['host'] = {}

        self.RequireSession()
        if self.session is not None:
            try:
                thisHost = self.session.xenapi.session.get_this_host(self.session._session)
                
                hostRecord = self.session.xenapi.host.get_record(thisHost)
                self.data['host'] = hostRecord
                self.data['host']['opaqueref'] = thisHost
                
                # Expand the items we need in the host record
                self.data['host']['metrics'] = self.session.xenapi.host_metrics.get_record(self.data['host']['metrics'])
                
                convertCPU = lambda cpu: self.session.xenapi.host_cpu.get_record(cpu)
                self.data['host']['host_CPUs'] = map(convertCPU, self.data['host']['host_CPUs'])
                
                def convertPIF(inPIF):
                    retVal = self.session.xenapi.PIF.get_record(inPIF)
                    retVal['metrics'] = self.session.xenapi.PIF_metrics.get_record(retVal['metrics'])
                    if retVal['network'] != 'OpaqueRef:NULL':
                        retVal['network'] = self.session.xenapi.network.get_record(retVal['network'])
                    retVal['opaqueref'] = inPIF
                    return retVal
    
                self.data['host']['PIFs'] = map(convertPIF, self.data['host']['PIFs'])
    
                # Sort PIFs by device name for consistent order
                self.data['host']['PIFs'].sort(lambda x, y : cmp(x['device'], y['device']))

                def convertVBD(inVBD):
                    retVBD = self.session.xenapi.VBD.get_record(inVBD)
                    retVBD['opaqueref'] = inVBD
                    return retVBD
                    
                def convertVDI(inVDI):
                    retVDI = self.session.xenapi.VDI.get_record(inVDI)
                    retVDI['VBDs'] = map(convertVBD, retVDI['VBDs'])
                    retVDI['opaqueref'] = inVDI
                    return retVDI
                    
                def convertPBD(inPBD):
                    retPBD = self.session.xenapi.PBD.get_record(inPBD)
                    if retPBD['SR'] != 'OpaqueRef:NULL':
                        srRef = retPBD['SR']
                        retPBD['SR'] = self.session.xenapi.SR.get_record(retPBD['SR'])
                        retPBD['SR']['VDIs'] = map(convertVDI, retPBD['SR']['VDIs'])
                        retPBD['SR']['opaqueref'] = srRef
                        
                    retPBD['opaqueref'] = inPBD
                    return retPBD
                    
                self.data['host']['PBDs'] = map(convertPBD, self.data['host']['PBDs'])

                # Only load the to DOM-0 VM to save time
                vmList = self.data['host']['resident_VMs']
                for i in range(len(vmList)):
                    vm = vmList[i]
                    domID = self.session.xenapi.VM.get_domid(vm)
                    if domID == '0':
                        vmList[i] = self.session.xenapi.VM.get_record(vm)
                        vmList[i]['allowed_VBD_devices'] = self.session.xenapi.VM.get_allowed_VBD_devices(vm)
                        vmList[i]['opaqueref'] = vm
                    
            except Exception, e:
                pass # Ignore failure - just leave data empty

        self.UpdateFromResolveConf()
        self.UpdateFromSysconfig()
        
        if os.path.isfile("/sbin/chkconfig"):
            (status, output) = commands.getstatusoutput("/sbin/chkconfig --list sshd")
            if status == 0:
                self.ScanChkConfig(output.split("\n"))

        self.DeriveData()
        
    def DeriveData(self):
        self.data.update({
            'derived' : {
                'cpu_name_summary' : {}
            }
        })
        
        # Gather up the CPU model names into a more convenient form
        if 'host_CPUs' in self.data['host']:
            hostCPUs = self.data['host']['host_CPUs']
    
            cpuNameSummary = self.data['derived']['cpu_name_summary']
            
            for cpu in hostCPUs:
                name = " ".join(cpu['modelname'].split())
                if name in cpuNameSummary:
                    cpuNameSummary[name] += 1
                else:
                    cpuNameSummary[name] = 1        
        
        # Select the current management PIFs
        self.data['derived']['managementpifs'] = []
        if 'PIFs' in self.data['host']:
            for pif in self.data['host']['PIFs']:
                if pif['management']:
                    self.data['derived']['managementpifs'].append(pif)
        
        # Add a reference to the DOM-0 VM
        if 'resident_VMs' in self.data['host']:
            for vm in self.data['host']['resident_VMs']:
                if 'domid' in vm and vm['domid'] == '0':
                    self.data['derived']['dom0_vm'] = vm
     
        # Calculate the full version string
        self.data['derived']['fullversion'] = (
            self.host.software_version.product_version('') + '-' +
            self.host.software_version.build_number('') + '-' +
            self.host.software_version.oem_build_number('')
        )
        if self.data['derived']['fullversion'] == '--':
            self.data['derived']['fullversion'] = Lang("<Unknown>")

    def Dump(self):
        pprint(self.data)

    def HostnameSet(self, inHostname):
        Auth.Inst().AssertAuthenticated()

        if not re.match(r'[-A-Za-z0-9.]+$', inHostname):
            raise Exception("Invalid hostname '"+inHostname+"'")
        
        self.RequireSession()
        
        self.session.xenapi.host.set_name_label(self.host.opaqueref(), inHostname)
        
        self.data['sysconfig']['network']['hostname'] = inHostname
        self.SaveToSysconfig()

        status, output = commands.getstatusoutput("/bin/hostname '"+inHostname+"'")
        if status != 0:
            raise Exception(output)


    def NameserversSet(self, inServers):
        self.data['dns']['nameservers'] = inServers

    def LoggingDestinationSet(self, inDestination):
        Auth.Inst().AssertAuthenticated()
        
        self.RequireSession()
        
        self.session.xenapi.host.remove_from_logging(self.host.opaqueref(), 'syslog_destination')
        self.session.xenapi.host.add_to_logging(self.host.opaqueref(), 'syslog_destination', inDestination)
        self.session.xenapi.host.syslog_reconfigure(self.host.opaqueref())
    
    def UpdateFromResolveConf(self):
        (status, output) = commands.getstatusoutput("/bin/cat /etc/resolv.conf")
        if status == 0:
            self.ScanResolvConf(output.split("\n"))
    
    def UpdateFromSysconfig(self):
        (status, output) = commands.getstatusoutput("/bin/cat /etc/sysconfig/network")
        if status == 0:
            self.ScanSysconfigNetwork(output.split("\n"))
            
    def SaveToResolvConf(self):
        # Double-check authentication
        Auth.Inst().AssertAuthenticated()
        
        file = None
        try:
            file = open("/etc/resolv.conf", "w")
            for other in self.dns.othercontents([]):
                file.write(other+"\n")
            for server in self.dns.nameservers([]):
                file.write("nameserver "+server+"\n")
        finally:
            if file is not None: file.close()
            self.UpdateFromResolveConf()

    def SaveToSysconfig(self):
        # Double-check authentication
        Auth.Inst().AssertAuthenticated()
        
        file = None
        try:
            file = open("/etc/sysconfig/network", "w")
            for other in self.sysconfig.network.othercontents([]):
                file.write(other+"\n")
            file.write("HOSTNAME="+self.sysconfig.network.hostname('')+"\n")
        finally:
            if file is not None: file.close()
            self.UpdateFromSysconfig()
    
    def ScanDmiDecode(self, inLines):
        STATE_NEXT_ELEMENT = 2
        state = 0
        
        self.data['dmi'] = {
            'cpu_sockets' : 0,
            'cpu_populated_sockets' : 0,
            'memory_sockets' : 0,
            'memory_modules' : 0,
            'memory_size' : 0
        }
        
        for line in inLines:
            indent = 0
            while len(line) > 0 and line[0] == "\t":
                indent += 1
                line = line[1:]
                    
            if indent == 0 and state > 3:
                state = STATE_NEXT_ELEMENT
                
            if state == 0:
                self.data['dmi']['dmi_banner'] = line
                state += 1
            elif state == 1:
                match = re.match(r'(SMBIOS\s+\S+).*', line)
                if match:
                    self.data['dmi']['smbios'] = match.group(1)
                    state += 1
            elif state == 2:
                # scan for 'Handle...' line
                if indent == 0 and re.match(r'Handle.*', line):
                    state += 1
            elif state == 3:
                if indent == 0:
                    elementName = line
                    if elementName == 'BIOS Information': state = 4
                    elif elementName == 'System Information': state = 5
                    elif elementName == 'Chassis Information': state = 6
                    elif elementName == 'Processor Information': state = 7
                    elif elementName == 'Memory Device': state = 8
                else:        
                    state = STATE_NEXT_ELEMENT
            elif state == 4: # BIOS Information
                self.Match(line, r'Vendor:\s*(.*?)\s*$', 'bios_vendor')
                self.Match(line, r'Version:\s*(.*?)\s*$', 'bios_version')
            elif state == 5: # System Information
                self.Match(line, r'Manufacturer:\s*(.*?)\s*$', 'system_manufacturer')
                self.Match(line, r'Product Name:\s*(.*?)\s*$', 'system_product_name')
                self.Match(line, r'Serial Number:\s*(.*?)\s*$', 'system_serial_number')
            elif state == 6: # Chassis information
                self.Match(line, r'Asset Tag:\s*(.*?)\s*$', 'asset_tag')
            elif state == 7: # Processor information
                if self.MultipleMatch(line, r'Socket Designation:\s*(.*?)\s*$', 'cpu_socket_designations'):
                    self.data['dmi']['cpu_sockets'] += 1
                if re.match(r'Status:.*Populated.*', line):
                    self.data['dmi']['cpu_populated_sockets'] += 1
            elif state == 8: # Memory Device
                if self.MultipleMatch(line, r'Locator:\s*(.*?)\s*$', 'memory_locators'):
                    self.data['dmi']['memory_sockets'] += 1
                match = self.MultipleMatch(line, r'Size:\s*(.*?)\s*$', 'memory_sizes')
                if match:
                    size = re.match(r'(\d+)\s+([MGBmgb]+)', match.group(1))
                    if size and size.group(2).lower() == 'mb':
                        self.data['dmi']['memory_size'] += int(size.group(1))
                        self.data['dmi']['memory_modules'] += 1
                    elif size and size.group(2).lower() == 'gb':
                        self.data['dmi']['memory'] += int(size.group(1)) * 1024
                        self.data['dmi']['memory_modules'] += 1
    
    def Match(self, inLine, inRegExp, inKey):
        match = re.match(inRegExp, inLine)
        if match:
            self.data['dmi'][inKey] = match.group(1)
        return match
    
    def MultipleMatch(self, inLine, inRegExp, inKey):
        match = re.match(inRegExp, inLine)
        if match:
            if not self.data['dmi'].has_key(inKey):
                self.data['dmi'][inKey] = []
            self.data['dmi'][inKey].append(match.group(1))

        return match

    def ScanLspci(self, inLines):
        self.data['lspci'] = {
            'storage_controllers' : []
        }
        # Spot storage controllers by looking for keywords or the phrase 'storage controller' in the lspci output
        keywords = "IDE|PATA|SATA|SCSI|SAS|RAID|Fiber Channel"
        for line in inLines:
            if not re.search(r'[Uu]nknown [Dd]evice', line): # Skip unknown devices
                match = re.match(r'[0-9a-f:.]+\s+(.*)', line)
                if match:
                    name = match.group(1)
                    match1 = re.match(r'('+keywords+')', name)
                    match2 = re.search(r'[Ss]torage [Cc]ontroller', name)
                    
                    if match1 or match2:
                        self.data['lspci']['storage_controllers'].append(name)
            
    def ScanIpmiMcInfo(self, inLines):
        self.data['bmc'] = {}

        for line in inLines:
            match = re.match(r'Firmware\s+Revision\s*:\s*([-0-9.]+)', line)
            if match:
                self.data['bmc']['version'] = match.group(1)
    
    def ScanChkConfig(self, inLines):
        self.data['chkconfig'] = {}

        for line in inLines:
            # Is sshd on for runlevel 5?
            if re.match(r'sshd.*5\s*:\s*on', line, re.IGNORECASE):
                self.data['chkconfig']['sshd'] = True
            elif re.match(r'sshd.*5\s*:\s*off', line, re.IGNORECASE):
                self.data['chkconfig']['sshd'] = False
            # else leave as Unknown
    
    def ScanResolvConf(self, inLines):
        self.data['dns'] = {
            'nameservers' : [], 
            'othercontents' : []
        }
        for line in inLines:
            match = re.match(r'nameserver\s+(\S+)',  line)
            if match:
                self.data['dns']['nameservers'].append(match.group(1))
            else:
                self.data['dns']['othercontents'].append(line)
    
    def ScanSysconfigNetwork(self, inLines):
        if not 'sysconfig' in self.data:
            self.data['sysconfig'] = {}
            
        self.data['sysconfig']['network'] = {'othercontents' : [] }
        
        for line in inLines:
            match = re.match(r'HOSTNAME\s*=\s*(.*)', line)
            if match:
                self.data['sysconfig']['network']['hostname'] = match.group(1)
            else:
                self.data['sysconfig']['network']['othercontents'].append(line)
    
    def ScanCPUInfo(self, inLines):
        self.data['cpuinfo'] = {}
        for line in inLines:
            match = re.match(r'flags\s*:\s*(.*)', line)
            if match:
                self.data['cpuinfo']['flags'] = match.group(1).split()

    def ReconfigureManagement(self, inPIF, inMode,  inIP,  inNetmask,  inGateway, inDNS = None):
        # Double-check authentication
        Auth.Inst().AssertAuthenticated()
        try:
            self.RequireSession()
            self.session.xenapi.PIF.reconfigure_ip(inPIF['opaqueref'],  inMode,  inIP,  inNetmask,  inGateway, FirstValue(inDNS, ''))
            self.session.xenapi.host.management_reconfigure(inPIF['opaqueref'])
        finally:
            # Network reconfigured so this link is potentially no longer valid
            self.session = Auth.Inst().CloseSession(self.session)
    
    def ConfigureRemoteShell(self, inEnable):
        if inEnable:
            status, output = commands.getstatusoutput("/sbin/chkconfig sshd on")
        else:
            status, output = commands.getstatusoutput("/sbin/chkconfig sshd off")
        
        if status != 0:
            raise Exception(output)
    
    def Ping(self,  inDest):
        # Must be careful that no unsanitised data is passed to the shell
        if not re.match(r'([-0-9a-zA-Z.]+)$',  inDest):
            raise Exception("Invalid destination '"+inDest+"'")
        
        command = "/bin/ping -c 1 -w 2 '"+inDest+"'"
        (status,  output) = commands.getstatusoutput(command)
        return (status == 0,  output)
    
    def ManagementIP(self, inDefault = None):
        retVal = inDefault
        
        retVal = self.host.address(retVal)
        
        return retVal

    def ManagementNetmask(self, inDefault = None):
        retVal = inDefault
        
        # FIXME: Address should come from API, but not available at present.  For DHCP this is just a guess at the gateway address
        for pif in self.derived.managementpifs([]):
            if pif['ip_configuration_mode'].lower().startswith('static'):
                # For static IP the API address is correct
                retVal = pif['netmask']
            elif pif['ip_configuration_mode'].lower().startswith('dhcp'):
                # For DHCP,  find the gateway address by parsing the output from the 'route' command
                if 'bridge' in pif['network']:
                    device = pif['network']['bridge']
                else:
                    device = pif['device']

                device = ShellUtils.MakeSafeParam(device)

                ipre = r'[0-9a-f.:]+'
                ifRE = re.compile(r'\s*inet\s+addr\s*:'+ipre+'\s+bcast\s*:\s*'+ipre+r'\s+mask\s*:\s*('+ipre+r')\s*$',
                    re.IGNORECASE)

                ifconfig = commands.getoutput("/sbin/ifconfig '"+device+"'").split("\n")
                for line in ifconfig:
                    match = ifRE.match(line)
                    if match:
                        retVal = match.group(1)
                        break
    
        return retVal
    
    def ManagementGateway(self, inDefault = None):
        retVal = inDefault
        
        # FIXME: Address should come from API, but not available at present.  For DHCP this is just a guess at the gateway address
        for pif in self.derived.managementpifs([]):
            if pif['ip_configuration_mode'].lower().startswith('static'):
                # For static IP the API address is correct
                retVal = pif['gateway']
            elif pif['ip_configuration_mode'].lower().startswith('dhcp'):
                # For DHCP,  find the gateway address by parsing the output from the 'route' command
                if 'bridge' in pif['network']:
                    device = pif['network']['bridge']
                else:
                    device = pif['device']
                routeRE = re.compile(r'([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+UG\s+\d+\s+\d+\s+\d+\s+'+device,
                    re.IGNORECASE)
    
                routes = commands.getoutput("/sbin/route -n").split("\n")
                for line in routes:
                    match = routeRE.match(line)
                    if match:
                        retVal = match.group(2)
                        break
    
        return retVal

    def VBDGetRecord(self, inVBD):
        self.RequireSession()

        vbdRecord = self.session.xenapi.VBD.get_record(inVBD)
        vbdRecord['opaqueref'] = inVBD
        
        return vbdRecord

    def CreateVBD(self, inVM, inVDI, inDeviceNum, inMode = None,  inType = None):
        self.RequireSession()
        
        vbd = {
            'VM' : inVM['opaqueref'],
            'VDI' : inVDI['opaqueref'], 
            'userdevice' : inDeviceNum, 
            'mode' : FirstValue(inMode, 'ro'),
            'bootable' : False, 
            'type' : FirstValue(inType, 'disk'), 
            'unpluggable' : True,
            'empty' : False, 
            'other_config' : { 'xsconsole_tmp' : 'Created: '+time.asctime(time.gmtime()) }, 
            'qos_algorithm_type' : '', 
            'qos_algorithm_params' : {}
        }

        newVBD = self.session.xenapi.VBD.create(vbd)

        return self.VBDGetRecord(newVBD)
    
    def PlugVBD(self, inVBD):
        self.session.xenapi.VBD.plug(inVBD['opaqueref'])
        # Must reread to get filled-in device field
        return self.VBDGetRecord(inVBD['opaqueref'])
        
    def UnplugVBD(self, inVBD):
        self.session.xenapi.VBD.unplug(inVBD['opaqueref'])
        return self.VBDGetRecord(inVBD['opaqueref'])

    def DestroyVBD(self, inVBD):
        self.session.xenapi.VBD.destroy(inVBD['opaqueref'])

    def PurgeVBDs(self):
        # Destroy any VBDs that xsconsole created but isn't using
        
        vbdRefs = {} # Use a dict to remove duplicates
        
        # Iterate through all VBDs we know about
        for pbd in Data.Inst().host.PBDs([]):
            sr = pbd.get('SR', {})
            for vdi in sr.get('VDIs', []):
                for vbd in vdi.get('VBDs', []):
                    if 'xsconsole_tmp' in vbd.get('other_config', {}):
                        vbdRefs[ vbd['opaqueref'] ] = vbd
        
        for vbd in vbdRefs.values():
            try:
                # Currently this won't destroy mounted VBDs
                if vbd['currently_attached']:
                    self.UnplugVBD(vbd)
                self.DestroyVBD(vbd)
            except Exception:
                pass # Fail silently
    
