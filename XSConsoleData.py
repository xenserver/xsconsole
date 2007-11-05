# import socket, fcntl, struct, os
import XenAPI
import commands, re,  sys

from pprint import pprint
from XSConsoleAuth import *

class DataMethod:
    def __init__(self, inSend, inName):
        self.send = inSend
        self.name = inName
        
    def __getattr__(self, inName):
        return DataMethod(self.send, self.name+[inName])

    def __call__(self):
        return self.send(self.name)

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
    
    def GetInfo(self, inKey):
        if inKey in self.data['dmi']:
            retVal = self.data['dmi'][inKey]
        else:
            retVal = 'Unknown'
        return retVal
    
    def RequireSession(self):
        if self.session is None: self.session = Auth.OpenSession()
    
    def Update(self):
        self.data = {
            'host' : {}
            }

        self.RequireSession()
        if self.session is not None:
            thisHost = self.session.xenapi.session.get_this_host(self.session._session)
            
            hostRecord = self.session.xenapi.host.get_record(thisHost)
            self.data['host'] = hostRecord

            # Expand the items we need in the host record
            self.data['host']['metrics'] = self.session.xenapi.host_metrics.get_record(self.data['host']['metrics'])
            
            convertCPU = lambda cpu: self.session.xenapi.host_cpu.get_record(cpu)
            self.data['host']['host_CPUs'] = map(convertCPU, self.data['host']['host_CPUs'])
            
            def convertPIF(inPIF):
                retVal = self.session.xenapi.PIF.get_record(inPIF)
                retVal['metrics'] = self.session.xenapi.PIF_metrics.get_record(retVal['metrics'])
                retVal['opaqueref'] = inPIF
                return retVal

            self.data['host']['PIFs'] = map(convertPIF, self.data['host']['PIFs'])

            # Sort PIFs by device name for consistent order
            self.data['host']['PIFs'].sort(lambda x, y : cmp(x['device'], y['device']))

            convertPBD = lambda pbd: self.session.xenapi.PBD.get_record(pbd)
            self.data['host']['PBDs'] = map(convertPBD, self.data['host']['PBDs'])

        (status, output) = commands.getstatusoutput("dmidecode")
        if status != 0:
            (status, output) = commands.getstatusoutput("cat ./dmidecode.txt")
            if status != 0:
                raise Exception("Cannot get dmidecode output")
        
        self.ScanDmiDecode(output.split("\n"))
     
        self.DeriveData()
        
    def DeriveData(self):
        self.data.update({
            'derived' : {
                'cpu_name_summary' : {}
            }
        })
        
        # Gather up the CPU model names info a more convinient form

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
        
    def GetData(self, inNames):
        data = self.data
        for name in inNames:
            if name is '__repr__':
                # Error - missing ()
                raise 'Data call Data.'+'.'.join(inNames[:-1])+' must end with ()'
            elif name is 'Size':
                data = len(data)
            elif name in data:
                data = data[name]
            else:
                return '<Unknown>'
        return data
    
    def __getattr__(self, inName):
        return DataMethod(self.GetData, [inName])
        
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

    def ReconfigureManagement(self, inPIF, inMode,  inIP,  inNetmask,  inGateway):
        try:
            self.RequireSession()
            self.session.xenapi.PIF.reconfigure_ip(inPIF['opaqueref'],  inMode,  inIP,  inNetmask,  inGateway)
            # Need to wait for DHCP?
            self.session.xenapi.host.management_reconfigure(inPIF['opaqueref'],  '') # TODO: Value for second parameter 'interface'
        finally:
            # Network reconfigured so this link is potentially no longer valid
            self.session = Auth.CloseSession(self.session)
        
    def Ping(self,  inIP):
        # Must be careful that no unsanitised data is passed to the shell
        # TODO: IP regexp will need revision for future IPv6 support
        match = re.match(r'([0-9]{1,3})\.([0-9]{1,3})\.([0-9]{1,3})\.([0-9]{1,3})',  inIP)
        if not match:
            raise Exception("Invalid IP address '"+inIP+'"')
        
        command = '/bin/ping -c 1 -w 2 -n '+match.group(1)+'.'+match.group(2)+'.'+match.group(3)+'.'+match.group(4)
        (status,  output) = commands.getstatusoutput(command)
        return (status == 0,  output)
        
