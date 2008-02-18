# Copyright (c) Citrix Systems 2007. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

import XenAPI

import commands, re, shutil, sys, tempfile
from pprint import pprint

from XSConsoleAuth import *
from XSConsoleRemoteDB import *
from XSConsoleKeymaps import *
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
    DISK_TIMEOUT_SECONDS = 60
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
        
        self.ReadTimezones()
        self.ReadKeymaps()
        
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
    
    def FakeMetrics(self, inPIF):
        retVal = {
            'carrier' : False,
            'device_name' : '',
            'vendor_name' : ''
            }
        return retVal
    
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
                
                try:
                    self.data['host']['suspend_image_sr'] = self.session.xenapi.SR.get_record(self.data['host']['suspend_image_sr'])
                except:
                    # NULL or dangling reference
                    self.data['host']['suspend_image_sr'] = None
                    
                try:
                    self.data['host']['crash_dump_sr'] = self.session.xenapi.SR.get_record(self.data['host']['crash_dump_sr'])
                except:
                    # NULL or dangling reference
                    self.data['host']['crash_dump_sr'] = None
                
                convertCPU = lambda cpu: self.session.xenapi.host_cpu.get_record(cpu)
                self.data['host']['host_CPUs'] = map(convertCPU, self.data['host']['host_CPUs'])
                
                def convertPIF(inPIF):
                    retVal = self.session.xenapi.PIF.get_record(inPIF)
                    try:
                        retVal['metrics'] = self.session.xenapi.PIF_metrics.get_record(retVal['metrics'])
                    except XenAPI.Failure:
                        retVal['metrics' ] = self.FakeMetrics(inPIF)
                    
                    try:
                        retVal['network'] = self.session.xenapi.network.get_record(retVal['network'])
                    except XenAPI.Failure, e:
                        pass # Ignore failure
                        
                    retVal['opaqueref'] = inPIF
                    return retVal
    
                self.data['host']['PIFs'] = map(convertPIF, self.data['host']['PIFs'])
    
                # Create missing PIF names
                for pif in self.data['host']['PIFs']:
                    if pif['metrics']['device_name'] == '':
                        if not pif['physical']:
                            # Bonded PIF
                            pif['metrics']['device_name'] = Lang("Virtual PIF within ")+pif['network'].get('name_label', Lang('<Unknown>'))
                        else:
                            pif['metrics']['device_name'] = Lang('<Unknown>')
    
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
                    srRef = retPBD['SR']
                    try:
                        retPBD['SR'] = self.session.xenapi.SR.get_record(retPBD['SR'])
                    except:
                        retPBD['SR'] = None # retPBD['SR'] is OpaqueRef:NULL
                        
                    if retPBD['SR'] is not None:
                        retPBD['SR']['VDIs'] = map(convertVDI, retPBD['SR']['VDIs'])
                        for vdi in retPBD['SR']['VDIs']:
                            vdi['SR'] = retPBD['SR']
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

            try:
                self.data['sr'] = []

                pbdRefs = []
                for pbd in self.data['host'].get('PBDs', []):
                    pbdRefs.append(pbd['opaqueref'])
                    
                srMap= self.session.xenapi.SR.get_all_records()
                for opaqueRef, values in srMap.iteritems():
                    values['opaqueref'] = opaqueRef
                    values['islocal'] = False
                    for pbdRef in values.get('PBDs', []):
                        if pbdRef in pbdRefs:
                            values['islocal'] = True
                            
                    self.data['sr'].append(values)
                    
            except:
                pass # Ignore failure - just leave data empty

        self.UpdateFromResolveConf()
        self.UpdateFromSysconfig()
        self.UpdateFromNTPConf()
        self.UpdateFromRemoteDBConf()
        self.UpdateFromPatchVersions()
        self.UpdateFromTimezone()
        self.UpdateFromKeymap()
        
        if os.path.isfile("/sbin/chkconfig"):
            (status, output) = commands.getstatusoutput("/sbin/chkconfig --list sshd && /sbin/chkconfig --list ntpd")
            if status == 0:
                self.ScanChkConfig(output.split("\n"))

        self.DeriveData()
        
    def DeriveData(self):
        self.data.update({
            'derived' : {
                'app_name' : Lang("XenCenter"),
                'full_app_name' : Lang("Citrix XenCenter"),
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
        
        # Don't treat name-label as hostname
        # self.session.xenapi.host.set_name_label(self.host.opaqueref(), inHostname)
        
        self.data['sysconfig']['network']['hostname'] = inHostname
        self.SaveToSysconfig()

        status, output = commands.getstatusoutput("/bin/hostname '"+inHostname+"'")
        if status != 0:
            raise Exception(output)

    def NameLabelSet(self, inNameLabel):
        self.RequireSession()
        self.session.xenapi.host.set_name_label(self.host.opaqueref(), inNameLabel)

    def NameserversSet(self, inServers):
        self.data['dns']['nameservers'] = inServers

    def NTPServersSet(self, inServers):
        self.data['ntp']['servers'] = inServers

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
    
    def UpdateFromNTPConf(self):
        (status, output) = commands.getstatusoutput("/bin/cat /etc/ntp.conf")
        if status == 0:
            self.ScanNTPConf(output.split("\n"))
            
    def StringToBool(self, inString):
        return inString.lower().startswith('true')

    def UpdateFromRemoteDBConf(self):
        self.data['remotedb'] = {}

        try:
            self.data['remotedb'] = RemoteDB.Inst().ReadConf()
            remoteDB = self.data['remotedb']
            
            # Translate string booleans to python booleans
            remoteDB['available_this_boot'] = self.StringToBool(remoteDB['available_this_boot'])
            remoteDB['is_on_remote_storage'] = self.StringToBool(remoteDB['is_on_remote_storage'])
            
        except Exception, e:
            remoteDB = { 'is_on_remote_storage' : False }
            
        try:
            self.data['remotedb']['defaultlocaliqn'] = RemoteDB.Inst().LocalIQN()
        except Exception, e:
            pass

    def RootLabel(self):
        output = commands.getoutput('/bin/cat /proc/cmdline')
        match = re.search(r'root=\s*LABEL\s*=\s*(\S+)', output)
        if match:
            retVal = match.group(1)
        else:
            retVal = 'xe-0x'
        return retVal

    def GetVersion(self, inLabel):
        match = re.match(r'(xe-|rt-)(\d+)[a-z]', inLabel)
        if match:
            retVal = int(match.group(2))
        else:
            retVal = 0
        
        return retVal

    def UpdateFromPatchVersions(self):
        command = '/sbin/findfs LABEL='+self.RootLabel()
        status, output = commands.getstatusoutput(command)
        bootDevice = None
        if status == 0:
            match = re.match(r'(.*)\d+$', output)
            if match:
                bootDevice = match.group(1)
            
        self.data['backup'] = {
            'bootdevice' : bootDevice,
            'canrevert' : False
        }
        
        if bootDevice is not None:
            sda1Version = self.GetVersion(commands.getoutput("/sbin/e2label "+bootDevice+"1"))
            sda2Version = self.GetVersion(commands.getoutput("/sbin/e2label "+bootDevice+"2"))
            currentVersion = self.GetVersion(self.RootLabel())
            self.data['backup']['currentlabel'] = currentVersion
            
            if currentVersion == sda1Version and sda2Version < sda1Version:
                self.data['backup']['canrevert'] = True
                self.data['backup']['revertto'] = 2
                self.data['backup']['previouslabel'] = sda2Version
            elif currentVersion == sda2Version and sda1Version < sda2Version:
                self.data['backup']['canrevert'] = True
                self.data['backup']['revertto'] = 1
                self.data['backup']['previouslabel'] = sda1Version

    def Revert(self):
        if self.backup.canrevert(False):
            status, output = commands.getstatusoutput("/opt/xensource/libexec/bootable.sh "+
                self.backup.bootdevice()+" "+str(self.backup.revertto()))
            if status != 0:
                raise Exception(output)
        else:
            raise Exception("Unable to revert")
            
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
    
    def SaveToNTPConf(self):
        # Double-check authentication
        Auth.Inst().AssertAuthenticated()
        
        file = None
        try:
            file = open("/etc/ntp.conf", "w")
            for other in self.ntp.othercontents([]):
                file.write(other+"\n")
            for server in self.ntp.servers([]):
                file.write("server "+server+"\n")
        finally:
            if file is not None: file.close()
            self.UpdateFromNTPConf()
    
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
            elif re.match(r'ntpd.*5\s*:\s*on', line, re.IGNORECASE):
                self.data['chkconfig']['ntpd'] = True
            elif re.match(r'ntpd.*5\s*:\s*off', line, re.IGNORECASE):
                self.data['chkconfig']['ntpd'] = False

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
    
    def ScanNTPConf(self, inLines):
        if not 'ntp' in self.data:
            self.data['ntp'] = {}
        
        self.data['ntp']['servers'] = []
        self.data['ntp']['othercontents'] = []
        
        for line in inLines:
            match = re.match(r'server\s+(\S+)', line)
            if match:
                self.data['ntp']['servers'].append(match.group(1))
            else:
                self.data['ntp']['othercontents'].append(line)
                
    def ScanCPUInfo(self, inLines):
        self.data['cpuinfo'] = {}
        for line in inLines:
            match = re.match(r'flags\s*:\s*(.*)', line)
            if match:
                self.data['cpuinfo']['flags'] = match.group(1).split()

    def ReadTimezones(self):
        self.data['timezones'] = {
            'continents': {
                Lang('Africa') : 'Africa',
                Lang('Americas') : 'America',
                Lang('US') : 'US',
                Lang('Canada') : 'Canada',
                Lang('Asia') : 'Asia',
                Lang('Atlantic Ocean') : 'Atlantic',
                Lang('Australia') : 'Australia',
                Lang('Europe') : 'Europe',
                Lang('Indian Ocean') : 'Indian',
                Lang('Pacific Ocean') : 'Pacific',
                Lang('Other') : 'Etc'
            },
            'cities' : {} 
        }
        
        filterExp = re.compile('('+'|'.join(self.data['timezones']['continents'].values())+')')

        zonePath = '/usr/share/zoneinfo'
        for root, dirs, files in os.walk(zonePath):
            for filename in files:
                filePath = os.path.join(root, filename)
                localPath = filePath[len(zonePath)+1:] # Just the path afer /usr/share/zoneinfo/
                if filterExp.match(localPath):
                    # Store only those entries starting with on of our known prefixes
                    self.data['timezones']['cities'][localPath] = filePath

    def UpdateFromTimezone(self):
        if os.path.isfile('/etc/timezone'):
            file = open('/etc/timezone')
            self.data['timezones']['current'] = file.readline().rstrip()
            file.close()

    def TimezoneSet(self, inTimezone):
        localtimeFile = '/etc/localtime'
        if os.path.isfile(localtimeFile):
            os.remove(localtimeFile)
        shutil.copy(self.timezones.cities({})[inTimezone], localtimeFile)
        
        file = open('/etc/timezone', 'w')
        file.write(inTimezone+"\n")
        file.close()
        
    def CurrentTimeString(self):
        return commands.getoutput('/bin/date -R')

    def ReadKeymaps(self):
        self.data['keyboard'] = {
            'keymaps' : {} 
        }

        keymapsPath = '/lib/kbd/keymaps/i386'
        excludeExp = re.compile(re.escape(keymapsPath)+r'/include')
        
        filterExp = re.compile(r'(.*).map.gz$')

        for root, dirs, files in os.walk(keymapsPath):
            for filename in files:
                if not excludeExp.match(root):
                    match = filterExp.match(filename)
                    if match:
                        filePath = os.path.join(root, filename)
                        self.data['keyboard']['keymaps'][match.group(1)] = filePath
        
        self.data['keyboard']['namestomaps'] = Keymaps.NamesToMaps()
        for value in self.data['keyboard']['namestomaps'].values():
            if not value in self.data['keyboard']['keymaps']:
                print "Warning: Missing keymap " + value
    
    def KeymapSet(self, inKeymap):
        # mapFile = self.keyboard.keymaps().get(inKeymap, None)
        # if mapFile is None:
        #     raise Exception(Lang("Unknown keymap '")+str(inKeymap)+"'")
        
        keymapParam = ShellUtils.MakeSafeParam(inKeymap)
        # Load the keymap now
        status, output = commands.getstatusoutput('/bin/loadkeys "'+keymapParam+'"')
        if status != 0:
            raise Exception(output)
        
        # Use state-based method to ensure that keymap is set on first run
        State.Inst().KeymapSet(keymapParam)

        # Store the keymap for next boot
        # Currently this has no effect
        file = open('/etc/sysconfig/keyboard', 'w')
        file.write('KEYTABLE="'+keymapParam+'"\n')
        file.close()
    
    def KeymapToName(self, inKeymap):
        # Derive a name to present to the user
        mapName = FirstValue(inKeymap, Lang('<Default>'))
        for key, value in self.keyboard.namestomaps({}).iteritems():
            if value == inKeymap:
                mapName = key
        
        return mapName
    
    def UpdateFromKeymap(self):
        keymap = State.Inst().Keymap()
        self.data['keyboard']['currentname'] = self.KeymapToName(keymap)
    
    def SuspendSRSet(self, inSR):
        # Double-check authentication
        Auth.Inst().AssertAuthenticated()
        self.RequireSession()
        self.session.xenapi.host.set_suspend_image_sr(self.host.opaqueref(None), inSR['opaqueref'])
    
    def CrashDumpSRSet(self, inSR):
        # Double-check authentication
        Auth.Inst().AssertAuthenticated()
        self.RequireSession()
        self.session.xenapi.host.set_crash_dump_sr(self.host.opaqueref(None), inSR['opaqueref'])
    
    def ReconfigureManagement(self, inPIF, inMode,  inIP,  inNetmask,  inGateway, inDNS = None):
        # Double-check authentication
        Auth.Inst().AssertAuthenticated()
        try:
            self.RequireSession()
            self.session.xenapi.PIF.reconfigure_ip(inPIF['opaqueref'],  inMode,  inIP,  inNetmask,  inGateway, FirstValue(inDNS, ''))
            self.session.xenapi.host.management_reconfigure(inPIF['opaqueref'])
            status, output = commands.getstatusoutput('/opt/xensource/bin/xe host-signal-networking-change')
            if status != 0:
                raise Exception(output)
        finally:
            # Network reconfigured so this link is potentially no longer valid
            self.session = Auth.Inst().CloseSession(self.session)

    
    def DisableManagement(self):
        # Double-check authentication
        Auth.Inst().AssertAuthenticated()
        try:
            self.RequireSession()
            # Disable management interfaces
            self.session.xenapi.host.management_disable()
            # Disable the PIF that the management interface was using
            for pif in self.derived.managementpifs([]):
                self.session.xenapi.PIF.reconfigure_ip(pif['opaqueref'], 'None','' ,'' ,'' ,'')
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
        def TimedOp():
            self.session.xenapi.VBD.plug(inVBD['opaqueref'])
            
        TimeUtils.TimeoutWrapper(TimedOp, self.DISK_TIMEOUT_SECONDS)
        
        # Must reread to get filled-in device fieldcat 
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
    
    def IsXAPIRunning(self):
        # Avoids /etc/init.d/xapi status as it corrupts the screen font and can error out with Errno 4: Interrupted system call
        status, output = commands.getstatusoutput("/sbin/pidof -s /opt/xensource/bin/xapi")
        return status == 0
        
    def StopXAPI(self):
        if self.IsXAPIRunning():
            State.Inst().WeStoppedXAPISet(True)
            State.Inst().SaveIfRequired()
        
            # Setting TERM=xterm prevents /etc/profile.d/lang.sh reconfiguring the screen font
            status, output = commands.getstatusoutput("(export TERM=xterm && /etc/init.d/xapi stop)")
            if status != 0:
                raise Exception(output)
                
    def StartXAPI(self):
        if not self.IsXAPIRunning():
            status, output = commands.getstatusoutput("(export TERM=xterm && /etc/init.d/xapi start)")
            if status != 0:
                raise Exception(output)
                
            State.Inst().WeStoppedXAPISet(False)
            State.Inst().SaveIfRequired()
    
    def EnableNTP(self):
        status, output = commands.getstatusoutput(
            "(export TERM=xterm && /sbin/chkconfig ntpd on && /etc/init.d/ntpd start)")
        if status != 0:
            raise Exception(output)
        
    def DisableNTP(self):
        status, output = commands.getstatusoutput(
            "(export TERM=xterm && /sbin/chkconfig ntpd off && /etc/init.d/ntpd stop)")
        if status != 0:
            raise Exception(output)

    def RestartNTP(self):
        status, output = commands.getstatusoutput("(export TERM=xterm && /etc/init.d/ntpd restart)")
        if status != 0:
            raise Exception(output)

    def NTPStatus(self):
        status, output = commands.getstatusoutput("/usr/bin/ntpstat")
        return output
            
    def SetVerboseBoot(self, inVerbose):
            mountPoint = tempfile.mktemp(".xsconsole")
            if not os.path.isdir(mountPoint):
                os.mkdir(mountPoint, 0700)
                
            try:
                status, output = commands.getstatusoutput("/bin/mount LABEL=IHVCONFIG "+mountPoint + " 2>&1")
                if status != 0:
                    raise Exception(output)
                    
                if inVerbose:
                    name = 'noisy'
                else:
                    name='quiet'
                    
                os.system('/bin/cp -f '+mountPoint+'/'+name+'.opt '+mountPoint+'/linux.opt')
                os.system('/bin/cp -f '+mountPoint+'/x'+name+'.opt '+mountPoint+'/xen.opt')

                State.Inst().VerboseBootSet(inVerbose)

            finally:
                commands.getstatusoutput("/bin/umount "+mountPoint + " 2>&1")
                time.sleep(2)
                os.rmdir(mountPoint)
                
