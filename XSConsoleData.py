# import socket, fcntl, struct, os
import XenAPI
import commands, re,  sys
from pprint import pprint

from XSConsoleAuth import *
from XSConsoleLang import *

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
            cls.instance.Update()
        return cls.instance
    
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
        return DataMethod(self.GetData, [inName])
    
    def RequireSession(self):
        if self.session is None: self.session = Auth.Inst().OpenSession()
    
    def Update(self):
        self.data = {
            'host' : {}
            }

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
                    if retVal['network'] != 'OpaqueRef:NULL': retVal['network'] = self.session.xenapi.network.get_record(retVal['network'])
                    retVal['opaqueref'] = inPIF
                    return retVal
    
                self.data['host']['PIFs'] = map(convertPIF, self.data['host']['PIFs'])
    
                # Sort PIFs by device name for consistent order
                self.data['host']['PIFs'].sort(lambda x, y : cmp(x['device'], y['device']))
    
                convertPBD = lambda pbd: self.session.xenapi.PBD.get_record(pbd)
                self.data['host']['PBDs'] = map(convertPBD, self.data['host']['PBDs'])

            except Exception, e:
                pass # Ignore failure - just leave data empty

        self.UpdateFromResolveConf()

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
                    
     
    def Dump(self):
        pprint(self.data)
        #pprint("\n\nMethod list:\n\n")
        #self.RequireSession()
        #if self.session is not None:
        #    pprint(self.session.xenapi.host.list_methods())

    def HostnameSet(self, inHostname):
        if not Auth.Inst().IsAuthenticated():
            raise Exception("Failed to set hostname - not authenticated")
        if not re.match(r'[A-Za-z0-9.-]+$', inHostname):
            raise Exception("Invalid hostname '"+inHostname+"'")
        
        self.RequireSession()
        
        self.session.xenapi.host.set_hostname(self.host.opaqueref(), inHostname)

    def NameserversSet(self, inServers):
        self.data['dns']['nameservers'] = inServers

    def ChangePassword(self,  inOldPassword, inNewPassword):
        session = Auth.Inst().TCPSession(inOldPassword)
        session.xenapi.session.change_password(inOldPassword, inNewPassword)
        # Caller handles exceptions

    def UpdateFromResolveConf(self):
        (status, output) = commands.getstatusoutput("/bin/cat /etc/resolv.conf")
        if status == 0:
            self.ScanResolvConf(output.split("\n"))
    
    def SaveToResolvConf(self):
        # Double-check authentication
        if not Auth.Inst().IsAuthenticated():
            raise Exception("Failed to save resolv.conf - not authenticated")
        
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
            if not re.search(r'[Uu]nknown [Dd]evice',  line): # Skip unknown devices
                match = re.match(r'[0-9a-f:.]+\s+(.*)',  line)
                name = match.group(1)
                match1 = re.match(r'('+keywords+')',  name)
                match2 = re.search(r'[Ss]torage [Cc]ontroller',  name)
                
                if match1 or match2:
                    self.data['lspci']['storage_controllers'].append(name)
            
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
                
    def ReconfigureManagement(self, inPIF, inMode,  inIP,  inNetmask,  inGateway):
        # Double-check authentication
        if not Auth.Inst().IsAuthenticated():
            raise Exception("Failed to reconfigure management - not authenticated")
        try:
            self.RequireSession()
            self.session.xenapi.PIF.reconfigure_ip(inPIF['opaqueref'],  inMode,  inIP,  inNetmask,  inGateway)
            self.session.xenapi.host.management_reconfigure(inPIF['opaqueref'])
        finally:
            # Network reconfigured so this link is potentially no longer valid
            self.session = Auth.Inst().CloseSession(self.session)
        
    def Ping(self,  inDest):
        # Must be careful that no unsanitised data is passed to the shell
        if not re.match(r'([0-9a-zA-Z.-]+)$',  inDest):
            raise Exception("Invalid destination '"+inDest+"'")
        
        command = "/bin/ping -c 1 -w 2 '"+inDest+"'"
        (status,  output) = commands.getstatusoutput(command)
        return (status == 0,  output)
    
    def ManagementGateway(self):
        retVal = None
        
        # FIXME: Address should come from API, but not available at present.  For DHCP this is just a guess at the gateway address
        if self.derived.managementpifs.Size() == 0:
            # No management i/f configured
            pass
        else:
            for pif in self.derived.managementpifs():
                if pif['ip_configuration_mode'].lower().startswith('static'):
                    # For static IP the API address is correct
                    retVal = pif['gateway']
                elif pif['ip_configuration_mode'].lower().startswith('dhcp'):
                    # For DHCP,  find the gateway address by parsing the output from the 'route' command
                    if 'bridge' in pif['network']:
                        device = pif['network']['bridge']
                    else:
                        device = pif['device']
                    routeRE = r'([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+UG\s+\d+\s+\d+\s+\d+\s+'+device
        
                    routes = commands.getoutput("/sbin/route -n").split("\n")
                    for line in routes:
                        m = re.match(routeRE, line)
                        if m:
                            retVal = m.group(2)
    
        return retVal

