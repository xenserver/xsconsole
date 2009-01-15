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
from XSConsoleKeymaps import *
from XSConsoleLang import *
from XSConsoleLog import *
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
    
    def DataCache(self):
        # Not for general use
        return self.data
    
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
        if self.session is None:
            self.session = Auth.Inst().OpenSession()
        return self.session
    
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
     
        (status, output) = commands.getstatusoutput("/sbin/lspci -m")
        if status != 0:
            (status, output) = commands.getstatusoutput("/usr/bin/lspci -m")

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

        (status, output) = commands.getstatusoutput("/usr/bin/openssl x509 -in /etc/xensource/xapi-ssl.pem -fingerprint -noout")
        if status == 0:
            fp = output.split("=")
            if len(fp) >= 2:
                self.data['sslfingerprint'] = fp[1]
            else:
                self.data['sslfingerprint'] = "<Unknown>"
 
        try:
            self.data['sshfingerprint'] = ShellPipe('/usr/bin/ssh-keygen', '-lf', '/etc/ssh/ssh_host_rsa_key.pub').AllOutput()[0].split(' ')[1]
        except:
            self.data['sshfingerprint'] = Lang('<Unknown>')
        
        try:
            self.data['state_on_usb_media'] = ( ShellPipe('/bin/bash', '-c', 'source /opt/xensource/libexec/oem-functions; if state_on_usb_media; then exit 1; else exit 0; fi').CallRC() != 0 )
        except:
            self.data['state_on_usb_media'] = True
    


        self.UpdateFromPatchVersions()
        self.Update()
    
    def FakeMetrics(self, inPIF):
        retVal = {
            'carrier' : False,
            'device_name' : '',
            'vendor_name' : ''
            }
        return retVal
    
    def CloseSession(self):
        if self.session is not None:
            self.session = Auth.Inst().CloseSession(self.session)
    
    def Update(self):
        self.data['host'] = {}

        self.RequireSession()
        if self.session is not None:
            try:
                try:
                    thisHost = self.session.xenapi.session.get_this_host(self.session._session)
                except XenAPI.Failure, e:
                    XSLog('Data update connection failed - retrying.  Exception was:', e)
                    self.session = Auth.Inst().CloseSession(self.session)
                    self.RequireSession()
                    if self.session is None:
                        raise Exception('Could not connect to local xapi')
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
                        XSLogError('Missing network record: ', e)
                        
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
                    
                    # Get VDIs for udev SRs only - a pool may have thousands of non-udev VDIs
                    if retPBD['SR'] is not None:
                        retPBD['SR']['opaqueref'] = srRef
                        if retPBD['SR'].get('type', '') == 'udev':
                            retPBD['SR']['VDIs'] = map(convertVDI, retPBD['SR']['VDIs'])
                            for vdi in retPBD['SR']['VDIs']:
                                vdi['SR'] = retPBD['SR']
                    
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
                
                pools = self.session.xenapi.pool.get_all_records()
                
                def convertPool(inID, inPool):
                    retPool = inPool
                    retPool['opaqueref'] = inID
                    try:
                        retPool['master_uuid'] = self.session.xenapi.host.get_uuid(inPool['master'])
                    except:
                        retPool['master_uuid'] = None

                    # SRs in the pool record are often apparently valid but dangling references.
                    # We fetch the uuid to determine whether the SRs are real.
                    try:
                        retPool['default_SR_uuid'] = self.session.xenapi.SR.get_uuid(inPool['default_SR'])
                    except:
                        retPool['default_SR_uuid'] = None

                    try:
                        retPool['suspend_image_SR_uuid'] = self.session.xenapi.SR.get_uuid(inPool['suspend_image_SR'])
                    except:
                        retPool['suspend_image_SR_uuid'] = None
                        
                    try:
                        retPool['crash_dump_SR_uuid'] = self.session.xenapi.SR.get_uuid(inPool['crash_dump_SR'])
                    except:
                        retPool['crash_dump_SR_uuid'] = None
                    return retPool
                
                self.data['pools'] = {}
                for id, pool in pools.iteritems():
                   self.data['pools'][id] = convertPool(id, pool)

            except Exception, e:
                XSLogError('Data update failed: ', e)

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
                    
            except Exception, e:
                XSLogError('SR data update failed: ', e)

        self.UpdateFromResolveConf()
        self.UpdateFromSysconfig()
        self.UpdateFromNTPConf()
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
        version = self.host.software_version.product_version('') + '-' + self.host.software_version.build_number('')
        oemBuildNumber = self.host.software_version.oem_build_number('')
        if oemBuildNumber != '':
            version += '-'+oemBuildNumber
        if version.startswith('-'):
            version = Lang("<Unknown>")
        self.data['derived']['fullversion'] = version

    def Dump(self):
        pprint(self.data)

    def HostnameSet(self, inHostname):
        Auth.Inst().AssertAuthenticated()

        # Protect from shell escapes
        if not re.match(r'[-A-Za-z0-9.]+$', inHostname):
            raise Exception("Invalid hostname '"+inHostname+"'")
        IPUtils.AssertValidNetworkName(inHostname)
        
        self.RequireSession()

        self.session.xenapi.host.set_hostname_live(self.host.opaqueref(), inHostname)

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
        self.data['backup'] = {}

        alternateVersion = None
        try:
            try:
                alternateDev = ShellPipe('/opt/xensource/libexec/find-partition', 'alternate').Stdout()[0].split(',')[0]
                alternateMount = tempfile.mkdtemp(".xsconsole")
    
                ShellPipe('/bin/mount', '-t', 'auto', '-o', 'ro', alternateDev, alternateMount).Call()
                
                rootfsDev = alternateMount + '/rootfs'
                if not os.path.isfile(rootfsDev):
                    inventoryMount = alternateMount
                else:
                    rootfsMount = tempfile.mkdtemp(".xsconsole")
                    ShellPipe('/bin/mount', '-t', 'squashfs', '-o', 'loop,ro', rootfsDev, rootfsMount).Call()
                    inventoryMount = rootfsMount

                inventoryFile = open(inventoryMount+'/etc/xensource-inventory')
    
                for line in inventoryFile:
                    match = re.match(r"\s*BUILD_NUMBER\s*=\s*'([^']*)'", line)
                    if match:
                        alternateVersion = match.group(1)
                        break
            except Exception, e:
                XSLog('UpdateFromPatchVersions failed: ', e)
        finally:
            # Undefined variables raise exceptions, so this code will only undo operations that succeeded
            try: inventoryFile.close()
            except: pass
            try: ShellPipe('/bin/umount', '-d', rootfsMount).Call() # -d for loopback device
            except: pass
            try: os.rmdir(rootfsMount)
            except: pass
            try: ShellPipe('/bin/umount', alternateMount).Call()
            except: pass
            try: os.rmdir(alternateMount)
            except: pass

        self.data['backup']['alternateversion'] = alternateVersion

    def CanRevert(self):
        # Revert if the alternate version is earlier than the current version.
        try:
            numCurrent = int(re.match(r'([0-9]+)', self.host.software_version.build_number()).group(1))
            numAlternate = int(re.match(r'([0-9]+)', self.backup.alternateversion()).group(1))
            retVal = (numAlternate < numCurrent)
        except:
            retVal = False
        return retVal

    def Revert(self):
        if self.CanRevert():
            ShellPipe('/opt/xensource/libexec/set-boot', 'alternate').Call()
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
        classExp = re.compile(r'([Ss]torage|IDE|PATA|SATA|SCSI|SAS|RAID|[Ff]iber [Cc]hannel)\s+[Cc]ontroller')
        nameExp = re.compile(r'IDE|PATA|SATA|SCSI|SAS|RAID|Fiber Channel')
        unknownExp = re.compile(r'[Uu]nknown [Dd]evice')
        regExp = re.compile(
            r'[^"]*' + # Bus position, etc.
            r'"([^"]*)"[^"]+' + # Class 
            r'"([^"]*)"[^"]+' + # Vendor 
            r'"([^"]*)"[^"]+' + # Device 
            r'"([^"]*)"[^"]+' + # SVendor 
            r'"([^"]*)"') # SDevice 
            
        for line in inLines:
            match = regExp.match(line)
            if match:
                devClass = match.group(1)
                devName = match.group(3)
                devSVendor = match.group(4)
                devSName = match.group(5)

                # Determine whether this device is a storage controller
                if (classExp.search(devClass) or
                    nameExp.search(devName) or
                    nameExp.search(devSName)):
                    # Device is a candidate for the list.  Do we have a useful name for it?  
                    if not unknownExp.search(devSName) and devSName != '':
                        self.data['lspci']['storage_controllers'].append((devClass, devSVendor+' '+devSName)) # Tuple so double brackets
                    elif not unknownExp.search(devName):
                        self.data['lspci']['storage_controllers'].append((devClass, devName)) # Tuple so double brackets
                    # otherwise don't add it at all
            
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
                XSLogError("Warning: Missing keymap " + value)
    
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
    
    def RemovePartitionSuffix(self, inDevice):
        regExpList = [
            r'(/dev/disk/by-id.*?)-part[0-9]+$',
            r'(/dev/cciss/.*?)p[0-9]+$',
            r'(/dev/.*?)[0-9]+$'
        ]
            
        retVal = inDevice
        for regExp in regExpList:
            match = re.match(regExp, inDevice)
            if match:
                retVal = match.group(1)
                break
        return retVal
        
    def GetSRFromDevice(self, inDevice):
        retVal = None

        for pbd in self.host.PBDs([]):
            device = pbd.get('device_config', {}).get('device', '')
            if self.RemovePartitionSuffix(device) == inDevice:
                # This is the PBD containing the device.  Does it have an SR?
                sr = pbd.get('SR', None)
                if sr.get('name_label', None) is not None:
                    retVal = sr
        return retVal
    
    def SetPoolSRIfRequired(self, inOpaqueRef):
        Auth.Inst().AssertAuthenticated()
        self.RequireSession()
        pool = self.GetPoolForThisHost()
        if pool is not None:
            if pool['default_SR_uuid'] is None:
                self.session.xenapi.pool.set_default_SR(pool['opaqueref'], inOpaqueRef)
            if pool['suspend_image_SR_uuid'] is None:
                self.session.xenapi.pool.set_suspend_image_SR(pool['opaqueref'], inOpaqueRef)
            if pool['crash_dump_SR_uuid'] is None:
                self.session.xenapi.pool.set_crash_dump_SR(pool['opaqueref'], inOpaqueRef)
    
    def SetPoolSRsFromDeviceIfNotSet(self, inDevice):
        sr = self.GetSRFromDevice(inDevice)
        if sr is None:
            raise Exception(Lang("Device does not have an associated SR"))

        self.SetPoolSRIfRequired(sr['opaqueref'])

    def GetPoolForThisHost(self):
        self.RequireSession()
        retVal = None
        for pool in self.pools({}).values():
            # Currently there is only one pool
            retVal = pool
            break
            
        return retVal
    
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
    
    def LocalHostEnable(self):
        Auth.Inst().AssertAuthenticatedOrPasswordUnset()
        self.RequireSession()
        self.session.xenapi.host.enable(self.host.opaqueref())
        
    def LocalHostDisable(self):
        Auth.Inst().AssertAuthenticatedOrPasswordUnset()
        self.RequireSession()
        self.session.xenapi.host.disable(self.host.opaqueref())

    def ConfigureRemoteShell(self, inEnable):
        if inEnable:
            status, output = commands.getstatusoutput("/sbin/chkconfig sshd on")
        else:
            status, output = commands.getstatusoutput("/sbin/chkconfig sshd off")
        
        if status != 0:
            raise Exception(output)
    
    def Ping(self,  inDest):
        # Must be careful that no unsanitised data is passed to the command
        if not re.match(r'[0-9a-zA-Z][-0-9a-zA-Z.]*$',  inDest):
            raise Exception("Invalid destination '"+inDest+"'")
        IPUtils.AssertValidNetworkName(inDest)
        pipe = ShellPipe('/bin/ping', '-c',  '1',  '-w', '2', inDest)
        status = pipe.CallRC()
        return (status == 0, "\n".join(pipe.AllOutput()))
    
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
            except Exception, e:
                XSLogError('VBD purge failed', e)
    
    def IsXAPIRunning(self):
        try:
            if ShellPipe('/sbin/pidof', '-s',  '/opt/xensource/bin/xapi').CallRC() == 0:
                retVal = True
            else:
                retVal = False
        except:
            retVal = False
        return retVal
        
    def StopXAPI(self):
        if self.IsXAPIRunning():
            State.Inst().WeStoppedXAPISet(True)
            State.Inst().SaveIfRequired()        
            ShellPipe('/etc/init.d/xapi', 'stop').Call()
                
    def StartXAPI(self):
        if not self.IsXAPIRunning():
            ShellPipe('/etc/init.d/xapi', 'start').Call()
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
        if inVerbose:
            name = 'noisy'
        else:
            name = 'quiet'

        status, output = commands.getstatusoutput(
            "(export TERM=xterm && /opt/xensource/libexec/set-boot " + name + ")")
        if status != 0:
            raise Exception(output)
            
        State.Inst().VerboseBootSet(inVerbose)
