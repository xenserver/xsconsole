# Copyright (c) Citrix Systems 2007. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

import os, re, tempfile

from XSConsoleBases import *
from XSConsoleData import *
from XSConsoleLang import *

# Utils that do not need to access XSConsoleData should go in XSConsoleUtils,
# so that XSConsoleData can use them without creating circular import problems

class FileUtils:
    @classmethod
    def DeviceList(cls):
        retVal = []
        
        # Device lists can change as, e.g. USB keys are plugged.  Out-of-date device lists are
        # problematic so always update here
        Data.Inst().Update()
        
        for pbd in Data.Inst().host.PBDs([]):
            sr = pbd.get('SR', {})
            for vdi in sr.get('VDIs', []):
                nameLabel = vdi.get('name_label', Lang('Unknown'))
                if re.match(r'(SCSI|USB)', nameLabel): # Skip if not USB or SCSI
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
    def AssertSafePath(cls, inPath):
        if not re.match(r'[-A-Za-z0-9/._~]*$', inPath):
            raise Exception("Invalid characters in path '"+inPath+"'")

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

class MountVDI:
    def __init__(self, inVDI, inMode = None):
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
            FileUtils.AssertSafePath(self.mountDev)
            self.mountPoint = tempfile.mktemp(".xsconsole")
            if not os.path.isdir(self.mountPoint):
                os.mkdir(self.mountPoint, 0700)

            status, output = commands.getstatusoutput("/bin/mount -t auto -o " + self.mode + ' ' +self.mountDev+" "+self.mountPoint + " 2>&1")
            if status != 0:
                raise Exception(output)
            
            self.mountedVBD = True

        except Exception, e:
            try:
                self.Unmount()
            except Exception:
                pass #  Report the original exception, not this one
            raise e
        
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
            status, output = commands.getstatusoutput("/bin/umount "+self.mountPoint +  " 2>&1")
            os.rmdir(self.mountPoint)
            self.mountedVBD = False
        if self.pluggedVBD:
            self.vbd = Data.Inst().UnplugVBD(self.vbd)
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
        
    
