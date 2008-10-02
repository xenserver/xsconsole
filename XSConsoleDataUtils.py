# Copyright (c) Citrix Systems 2007. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

import os, popen2, re, tempfile

from XSConsoleBases import *
from XSConsoleData import *
from XSConsoleHotData import *
from XSConsoleLang import *
from XSConsoleLog import *

# Utils that do not need to access XSConsoleData should go in XSConsoleUtils,
# so that XSConsoleData can use them without creating circular import problems

#Exception classes
class USBNotFormatted(Exception):
    pass
    
class USBNotMountable(Exception):
    pass

class FileUtils:
    @classmethod
    def DeviceList(cls, inWritableOnly):
        retVal = []
        
        # Device lists can change as, e.g. USB keys are plugged.  Out-of-date device lists are
        # problematic so always update here
        Data.Inst().Update()
        
        for pbd in Data.Inst().host.PBDs([]):
            sr = pbd.get('SR', {})
            contentType = sr.get('content_type', '')
            if sr.get('type', '') == 'udev' and contentType in [ 'disk', 'iso' ]:
                # Scan only SRs with type 'udev' and content type 'disk' or 'iso'
                for vdi in sr.get('VDIs', []):
                    nameLabel = vdi.get('name_label', Lang('Unknown'))
                    readOnly = vdi.get('read_only', False)
                    if inWritableOnly and readOnly:
                        pass # Skip this VDI because we can't write to it (but need to)
                    else:
                        match = True
                        while match:
                            match = re.match(r'(.*):0$', nameLabel)
                            if match:
                                # Remove multiple trailing :0
                                nameLabel = match.group(1)
                        nameDesc = vdi.get('name_description', Lang('Unknown device'))
                        match = re.match(r'(.*)\srev\b', nameDesc)
                        if match:
                            # Remove revision information
                            nameDesc = match.group(1)
                            
                        deviceSize = int(vdi.get('physical_utilisation', 0))
                        if deviceSize < 0:
                            deviceSize = int(vdi.get('virtual_size', 0))
    
                        nameSize = cls.SizeString(deviceSize)
                        
                        name =  "%-50s%10.10s%10.10s" % (nameDesc[:50], nameLabel[:10], nameSize[:10])
                        retVal.append(Struct(name = name, vdi = vdi))

        retVal.sort(lambda x, y : cmp(x.vdi['name_label'], y.vdi['name_label']))

        return retVal

    @classmethod
    def SRDeviceList(self):
        retVal= []
        status, output = commands.getstatusoutput("/opt/xensource/libexec/list_local_disks")
        if status == 0:
            regExp = re.compile(r"\s*\(\s*'([^']*)'\s*,\s*'([^']*)'\s*,\s*'([^']*)'\s*,\s*'([^']*)'\s*,\s*'([^']*)'\s*\)")
            for line in output.split("\n"):
                match = regExp.match(line)
                if match:
                    retVal.append(Struct(
                        device = match.group(1),
                        bus = match.group(2),
                        empty = match.group(3),
                        size = int(match.group(4)),
                        name = match.group(5)
                        ))

        return retVal

    @classmethod
    def AssertSafePath(cls, inPath):
        if not re.match(r'[-A-Za-z0-9/._~ ]*$', inPath):
            raise Exception("Invalid characters in path '"+inPath+"'")
            
    @classmethod
    def AssertSafeLeafname(cls, inPath):
        cls.AssertSafePath(inPath)
        if re.match(r'\.\.', inPath) or re.search(r'/\.\.', inPath):
            raise Exception(Lang("Filenames containing .. are not allowed"))
        if re.match(r'\s*/', inPath):
            raise Exception(Lang("Absolute paths are not allowed"))

    @classmethod
    def SizeString(cls, inSizeOrFilename, inDefault = None):
        try:
            if isinstance(inSizeOrFilename, str):
                fileSize = os.path.getsize(inSizeOrFilename)
            else:
                fileSize = inSizeOrFilename
            
            # Using these values gives the expected values for USB sticks
            if fileSize >= 1000000000: # 1GB
                if fileSize < 10000000000: # 10GB
                    retVal = ('%.1f' % (int(fileSize / 100000000) / 10.0)) + Lang('GB') # e.g. 2.3GB
                else:
                    retVal = str(int(fileSize / 1000000000))+Lang('GB')
            elif fileSize >= 2000000:
                retVal = str(int(fileSize / 1000000))+Lang('MB')
            elif fileSize >= 2000:
                retVal = str(int(fileSize / 1000))+Lang('KB')
            else:
                retVal = str(int(fileSize))
            
        except Exception, e:
            retVal = FirstValue(inDefault, '')
        
        return retVal

    @classmethod
    def DeviceFromVDI(self, inVDI):
        retVal = inVDI['location']
        if os.path.islink(retVal):
            link = os.readlink(retVal)
            if os.path.isabs(link):
                retVal = link
            else:
                retVal = os.path.abspath(os.path.join(os.path.dirname(retVal), link))
            
        return retVal

    @classmethod
    def USBFormat(self, inVDI):
        realDevice = self.DeviceFromVDI(inVDI)
        partitionName = realDevice+'1'
        
        # Write the partition table with one FAT32 partition filling the disk
        popenObj = popen2.Popen4("/sbin/sfdisk --DOS --quiet '"+realDevice+"'")
        popenObj.tochild.write(",,0C\n") # First partition, 0x0C => Windows LBA partition type
        popenObj.tochild.write(";\n")
        popenObj.tochild.write(";\n")
        popenObj.tochild.write(";\n")
        popenObj.tochild.close() # Send EOF
        
        while True:
            try:
                popenObj.wait() # Must wait for completion before mkfs
                break
            except IOError, e:
                if e.errno != errno.EINTR: # Loop if EINTR
                    raise
                
        status, output = commands.getstatusoutput('/bin/sync')
        
        if status != 0:
            raise Exception(output)
        
        # Format the new partition with VFAT
        status, output = commands.getstatusoutput("/sbin/mkfs.vfat -n 'XenServer Backup' -F 32 '" +partitionName + "' 2>&1")
        
        if status != 0:
            raise Exception(output)
            
        status, output = commands.getstatusoutput('/bin/sync')
        
        if status != 0:
            raise Exception(output)

    @classmethod
    def BugReportFilename(cls):
        return Data.Inst().host.hostname('bugreport')+'-'+time.strftime("%Y%m%d%H%M%S", time.gmtime())+'Z.bugrpt'

class MountVDI:
    def __init__(self, inVDI, inMode = None):
        self.vdi = inVDI
        self.mountPoint = None
        self.vbd = None
        self.mode = FirstValue(inMode, 'ro')
        
        # Keep records of whether we created and plugged the VBD, for undoing it later
        self.createdVBD = False
        self.pluggedVBD = False
        self.mountedVBD = False
        data = Data.Inst()
        data.Update() # Get current device list
        
        try:
            vbdFound = None
            allowedVBDs = data.derived.dom0_vm.allowed_VBD_devices([])
            if len(allowedVBDs) == 0:
                data.PurgeVBDs()
                raise Exception("VBDs exhausted - please retry")
                
            for vbd in inVDI.get('VBDs', []):
                if vbd['userdevice'] in allowedVBDs:
                    # Already mounted in userspace, so reuse.  This case is probably never triggered
                    vbdFound = vbd
                    break
            
            if vbdFound is not None:
                self.vbd = vbdFound
            else:
                deviceNum = data.derived.dom0_vm.allowed_VBD_devices([])[-1] # Highest allowed device number
                self.vbd = data.CreateVBD(data.derived.dom0_vm(), inVDI, deviceNum, self.mode)
                self.createdVBD = True
                
            if not self.vbd['currently_attached']:
                self.vbd = data.PlugVBD(self.vbd)
                self.pluggedVBD = True
        
            self.mountDev = '/dev/'+self.vbd['device']
            
            time.sleep(1) # Wait a moment for xapi to create the nodes in /dev
            
            if os.path.exists(self.mountDev+'1'): # First partition
                self.mountDev += '1'
                
            FileUtils.AssertSafePath(self.mountDev)
            self.mountPoint = tempfile.mktemp(".xsconsole")
            if not os.path.isdir(self.mountPoint):
                os.mkdir(self.mountPoint, 0700)

            status, output = commands.getstatusoutput("/bin/mount -t auto -o " + self.mode + ' ' +self.mountDev+" "+self.mountPoint + " 2>&1")
            if status != 0:
                try:
                    self.Unmount()
                except Exception, e:
                    XSLogFailure('Device failed to unmount', e)
                output += '\n'+self.mountDev
                self.HandleMountFailure(output.split("\n"))
            
            self.mountedVBD = True

        except Exception, e:
            try:
                self.Unmount()
            except Exception, e:
                #  Report the original exception, not this one
                XSLogFailure('Device failed to unmount', e)
            raise e
        
    def HandleMountFailure(self, inOutput):
        # Entered after self.Unmount has run
        if self.vdi['SR']['type'] != 'udev' or self.vdi['SR']['content_type'] != 'disk':
            # Take special action for USB devices only, i.e. don't reformat SCSI disks, etc.
            raise Exception(inOutput)
        
        if self.mode != 'rw':
            # Don't reformat media unless we're planning to write to it
            raise Exception(Lang('This media is not readable.'))
        
        needsType = False
        for line in inOutput:
            if re.search(r'you must specify the filesystem type', line, re.IGNORECASE):
                needsType = True
    
        if not needsType:
            # Unrecognised failure
            raise Exception(inOutput)
        
        realDevice = FileUtils.DeviceFromVDI(self.vdi)
        status, output = commands.getstatusoutput("/sbin/fdisk -l '" +realDevice+"'")
        if status != 0:
            raise Exception(output)
            
        unformatted = False
        for line in output.split("\n"):
            if re.search(r"doesn't contain a valid partition table", line, re.IGNORECASE):
                unformatted = True
            if re.match(r'/dev/\w+\s+\*', line, re.IGNORECASE):
                # Bootable partition - leave this media alone
                raise Exception("This USB media is not mountable but has a bootable partition.  Please reformat it before use.")
        
        if unformatted:
            # Not formatted
            raise USBNotFormatted("USB media not formatted")
        else:
            # Formatted but doesn't mount
            raise USBNotMountable("USB media not mountable")
    
    def Scan(self, inRegExp = None, inNumToReturn = None):
        retVal = []
        numToReturn = FirstValue(inNumToReturn, 10)
        regExp = re.compile(FirstValue(inRegExp, r'.*'), re.IGNORECASE)
        for root, dirs, files in os.walk(self.mountPoint):
            if len(retVal) >= numToReturn:
                break
            for filename in files:
                if regExp.match(filename):
                    retVal.append(os.path.join(root, filename)[len(self.mountPoint)+1:])
                    if len(retVal) >= numToReturn:
                        break
                        
        return retVal
        
    def Unmount(self):
        status = 0
        if self.mountedVBD:
            status, output = commands.getstatusoutput("/bin/umount '"+self.mountPoint +  "' 2>&1")
            os.rmdir(self.mountPoint)
            self.mountedVBD = False
        if self.pluggedVBD:
            try:
                self.vbd = Data.Inst().UnplugVBD(self.vbd)
            except Exception:
                # Assume umount needs more time to complete so wait and try again
                time.sleep(5)
                try:
                    self.vbd = Data.Inst().UnplugVBD(self.vbd)
                except Exception, e:
                    XSLogFailure('Device failed to unmount', e)
                
            self.pluggedVBD = False
        if self.createdVBD:
            Data.Inst().DestroyVBD(self.vbd)
            self.createdVBD = False
        if status != 0:
            raise Exception(output)
    
    def MountedPath(self, inLeafname):
        return self.mountPoint + '/' + inLeafname
    
    def SizeString(self, inFilename, inDefault = None):
        return FileUtils.SizeString(self.MountedPath(inFilename), inDefault)
        
        
class MountVDIDirectly:
    def __init__(self, inVDI, inMode = None):
        self.vdi = inVDI
        self.mountPoint = None
        self.mode = FirstValue(inMode, 'ro')
        self.mountedVDI = False
    
        data = Data.Inst()
        data.Update() # Get current device list
        
        try:
            self.mountDev = FileUtils.DeviceFromVDI(self.vdi)
            
            if os.path.exists(self.mountDev+'1'): # First partition
                self.mountDev += '1'
                
            FileUtils.AssertSafePath(self.mountDev)
            self.mountPoint = tempfile.mktemp(".xsconsole")
            if not os.path.isdir(self.mountPoint):
                os.mkdir(self.mountPoint, 0700)

            status, output = commands.getstatusoutput("/bin/mount -t auto -o " + self.mode + ' ' +self.mountDev+" "+self.mountPoint + " 2>&1")
            if status != 0:
                try:
                    self.Unmount()
                except Exception, e:
                    XSLogFailure('Device failed to unmount', e)
                output += '\n'+self.mountDev
                self.HandleMountFailure(status, output.split("\n"))
            
            self.mountedVDI = True

        except Exception, e:
            try:
                self.Unmount()
            except Exception, e:
                XSLogFailure('Device failed to unmount', e)
            raise e
        
    def HandleMountFailure(self, inStatus, inOutput):
        # Entered after self.Unmount has run
        if self.vdi['SR']['type'] != 'udev' or self.vdi['SR']['content_type'] != 'disk':
            # Take special action for USB devices only, i.e. don't reformat SCSI disks, etc.
            if inStatus == 8192: # Return code for empty CD drive
                raise Exception(Lang("Drive is empty"))
            raise Exception(inOutput)
        
        if self.mode != 'rw':
            # Don't reformat media unless we're planning to write to it
            raise Exception(Lang('This media is not readable.'))
        
        needsType = False
        for line in inOutput:
            if re.search(r'you must specify the filesystem type', line, re.IGNORECASE):
                needsType = True
    
        if not needsType:
            # Unrecognised failure
            raise Exception(inOutput)
        
        realDevice = FileUtils.DeviceFromVDI(self.vdi)
        status, output = commands.getstatusoutput("/sbin/fdisk -l '" +realDevice+"'")
        if status != 0:
            raise Exception(output)
            
        unformatted = False
        for line in output.split("\n"):
            if re.search(r"doesn't contain a valid partition table", line, re.IGNORECASE):
                unformatted = True
            if re.match(r'/dev/\w+\s+\*', line, re.IGNORECASE):
                # Bootable partition - leave this media alone
                raise Exception("This USB media is not mountable but has a bootable partition.  Please reformat it before use.")
        
        if unformatted:
            # Not formatted
            raise USBNotFormatted("USB media not formatted")
        else:
            # Formatted but doesn't mount
            raise USBNotMountable("USB media not mountable")
    
    def Scan(self, inRegExp = None, inNumToReturn = None):
        retVal = []
        numToReturn = FirstValue(inNumToReturn, 10)
        regExp = re.compile(FirstValue(inRegExp, r'.*'), re.IGNORECASE)
        for root, dirs, files in os.walk(self.mountPoint):
            if len(retVal) >= numToReturn:
                break
            for filename in files:
                if regExp.match(filename):
                    retVal.append(os.path.join(root, filename)[len(self.mountPoint)+1:])
                    if len(retVal) >= numToReturn:
                        break
                        
        return retVal
        
    def Unmount(self):
        status = 0
        if self.mountedVDI:
            status, output = commands.getstatusoutput("/bin/umount '"+self.mountPoint +  "' 2>&1")
            os.rmdir(self.mountPoint)
            self.mountedVDI = False
        if status != 0:
            raise Exception(output)
    
    def MountedPath(self, inLeafname):
        return self.mountPoint + '/' + inLeafname
    
    def SizeString(self, inFilename, inDefault = None):
        return FileUtils.SizeString(self.MountedPath(inFilename), inDefault)                
        
class SRDataUtils:
    @classmethod
    def SRList(cls, inMode = None, inCapabilities = None):
        
        retVal = []
        for sr in HotAccessor().visible_sr:

            name = sr.name_label(Lang('<Unknown>'))
            
            if inMode != 'rw' or sr.content_type('') not in ['iso']:
                if inCapabilities is None or inCapabilities in sr.allowed_operations([]):
                    # Generate a Data-style record from the HotData one (backwards compatibility)
                    dataSR = copy.copy(sr()) # Shallow copy
                    dataSR['opaqueref'] = sr.HotOpaqueRef().OpaqueRef()
                    retVal.append( Struct(name = name, sr = dataSR) )

        retVal.sort(lambda x, y : cmp(x.name, y.name))

        return retVal
