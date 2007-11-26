
import tempfile

from XSConsoleBases import *
from XSConsoleData import *
from XSConsoleLang import *


class FileUtils:
    @classmethod
    def PatchDeviceList(cls):
        retVal = []
        
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
        self.mode = FirstValue(inMode, 'ro')
        data = Data.Inst()
        deviceNum = data.derived.dom0_vm.allowed_VBD_devices([])[-1]
        self.vbd = data.CreateVBD(data.derived.dom0_vm(), inVDI, deviceNum, self.mode)
        try:
            self.mountDev = '/dev/'+self.vbd['device']
            FileUtils.AssertSafePath(self.mountDev)
            self.mountPoint = tempfile.mktemp(".xsconsole")
            if not os.path.isdir(self.mountPoint):
                os.mkdir(self.mountPoint, 0700)
            
            status, output = 1, ""
            i=0
            while status != 0:
                status, output = commands.getstatusoutput("/bin/mount -t auto -o " + self.mode + ' ' +self.mountDev+" "+self.mountPoint + " 2>&1")
                if status != 0:
                    if i == 0: # First failure - try umounting our mount point
                        commands.getstatusoutput("/bin/umount " + self.mountPoint + " 2>&1")
                    elif i == 1: # Second failure - try umounting the device
                        commands.getstatusoutput("/bin/umount " + self.mountDev + " 2>&1")
                    else:
                        raise Exception(output)
                        
                i += 1
        except Exception, e:
            Data.Inst().DestroyVBD(self.vbd)
            self.vbd = None
            raise
        
    def Scan(self, inRegExp = None, inNumToReturn = None):
        retVal = []
        numToReturn = FirstValue(inNumToReturn, 10)
        regExp = re.compile(FirstValue(inRegExp, r'.*'))
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
        status, output = commands.getstatusoutput("/bin/umount "+self.mountPoint +  " 2>&1")
        if self.vbd is not None:
            Data.Inst().DestroyVBD(self.vbd)
            self.vbd = None
        if status != 0:
            raise Exception(output)
        if self.mountPoint is not None:
            os.rmdir(self.mountPoint)
    
    def MountedPath(self, inLeafname):
        return self.mountPoint + '/' + inLeafname
    
    def SizeString(self, inFilename, inDefault = None):
        return FileUtils.SizeString(self.MountedPath(inFilename), inDefault)
