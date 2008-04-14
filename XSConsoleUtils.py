# Copyright (c) Citrix Systems 2007. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

import re, signal, string, subprocess, time, types
from pprint import pprint

from XSConsoleLang import *

# Utils that need to access Data must go in XSConsoleDataUtils,
# and XSConsoleData can't use anything in XSConsoleDataUtils without creating
# circular import problems


# Using ShellPipe:
# ShellPipe("/etc/init.d/xapi", "start").Call()
# if ShellPipe("/etc/init.d/ntp", "status").CallRC() != 0:
# message = ShellPipe("/bin/ping","-c", "1", "citrix.com").Stdout()
# message = ShellPipe("/bin/ping -c 1 -n citrix.com".split()).Stdout()
#
# pipe = ShellPipe("/bin/ping","-c", "10", "citrix.com").Stdout() # Ping starts immediately
#   ... do something else for 10 seconds ...
# message = pipe.Stdout() # Collect output (will return quickly)

# Experimental features:
# Chain: Run one after the other whilst commands succeed, and collect all output (like bash && )
# ShellPipe("nslookup", "citrix.com").Chain("nslookup", "citrixxenserver.com").Stdout())
#
# Pipe: Feed the output from one command into the input of the other (like bash | )
# ShellPipe("cat", "/etc/passwd").Pipe("grep", "root").Stdout()
#
# Note: ShellPipe does not use /bin/sh so sh-like features are not available

class ShellPipe:
    def __init__(self, *inParams):
        self._NewPipe(*inParams)
        self.stdout = []
        self.stderr = []
        self.called = False
        
    def _NewPipe(self, *inParams):
        if len(inParams) == 1 and isinstance(inParams, (types.ListType, types.TupleType)):
                params = inParams[0]
        else:
            params = inParams
            
        self.pipe = subprocess.Popen(params,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            close_fds=True)
        self.called = False
    
    def Stdout(self):
        if not self.called:
            self.Call()
        return self.stdout
        
    def Stderr(self):
        if not self.called:
            self.Call()
        return self.stderr
    
    def AllOutput(self):
        if not self.called:
            self.Call()
        return self.stdout + self.stderr
    
    def Communicate(self, inInput = None):
        if self.called:
            raise Exception("ShellPipe called more than once")
        self.called = True
        while True:
            try:
                if isinstance(inInput, (types.ListType, types.TupleType)):
                    stdout, stderr = self.pipe.communicate("\n".join(inInput))
                else:
                    stdout, stderr = self.pipe.communicate(inInput)
                    
                self.stdout += stdout.splitlines()
                self.stderr += stderr.splitlines()
                break
            except IOError, e:
                if e.errno != errno.EINTR: # Loop if EINTR
                    raise
            # Other exceptions propagate to the caller
        
    def CallRC(self, inInput = None): # Raise exception or return the return code
        self.Communicate(inInput)
        return self.pipe.returncode
    
    def Call(self, inInput = None): # Raise exception on failure
        self.Communicate(inInput)
        if self.pipe.returncode != 0:
            if len(self.stderr) > 0:
                raise Exception("\n".join(self.stderr))
            if len(self.stdout) > 0:
                raise Exception("\n".join(self.stdout))
            else:
                raise Exception("Unknown failure")
        return self
    
    def Chain(self, *inParams):
        if not self.called:
            self.Call()
        self._NewPipe(*inParams)
        self.Call()
        return self
    
    def Pipe(self, *inParams):
        if not self.called:
            self.Call()
        newInput = self.stdout
        self._NewPipe(*inParams)
        self.stdout = []
        self.Call(newInput)
        return self


class ShellUtils:
    @classmethod
    def MakeSafeParam(cls, inParam):
        if not re.match(r'[-A-Za-z0-9/._~:@]*$', inParam):
            raise Exception("Invalid characters in parameter '"+inParam+"'")
        return inParam
        
    @classmethod
    def WaitOnPipe(cls, inPipe):
        # Wait on a popen2 pipe, handling Interrupted System Call exceptions
        while True:
            try:
                inPipe.wait()
                break
            except IOError, e:
                if e.errno != errno.EINTR: # Loop if EINTR
                    raise

class TimeException(Exception):
    pass

class TimeUtils:
    @staticmethod
    def AlarmHandler(inSigNum, inStackFrame):
        raise TimeException("Operation timed out")
        
    @classmethod
    def TimeoutWrapper(cls, inCallable, inTimeout):
        oldHandler = signal.signal(signal.SIGALRM, TimeUtils.AlarmHandler)
        signal.alarm(inTimeout)
        try:
            inCallable()
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, oldHandler)
            
    @classmethod
    def DurationString(cls, inSecs):
        secs = max(0, int(inSecs))
        
        hours = int(secs / 3600)
        secs -= hours * 3600
        mins = int(secs / 60)
        secs -= mins * 60
        if hours > 0:
            retVal = "%d:%2.2d:%2.2d" % (hours, mins, secs)
        else:
            retVal = "%d:%2.2d" % (mins, secs)
        return retVal
        
    @classmethod
    def DateTimeToSecs(cls, inDateTime):
        structTime = time.strptime(inDateTime.value, '%Y%m%dT%H:%M:%SZ')
        retVal = time.mktime(structTime)
        if retVal <= 3601.0: # Handle the effect of daylight savings on start of epoch
            retVal = 0.0
        return retVal
    
class IPUtils:
    @classmethod
    def ValidateIP(cls, text):
        rc = re.match("^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$", text)
        if not rc: return False
        ints = map(int, rc.groups())
        largest = 0
        for i in ints:
            if i > 255: return False
            largest = max(largest, i)
        if largest is 0: return False
        return True
    
class SizeUtils:
    @classmethod
    def MemorySizeString(cls, inBytes):
        bytes = int(inBytes)
            
        # Memory is always KiB/MiB/GiB
        if bytes is None or bytes < 0:
            retVal = Lang('<Unknown>')
        elif bytes >= 1073741824: # 1GiB
            if bytes < 10737418240: # 10GiB
                retVal = ('%.1f' % (int(bytes / 107374182.4) / 10.0)) + Lang('GB') # e.g. 2.3GiB
            else:
                retVal = str(int(bytes / 1073741824))+Lang('GB')
        elif bytes >= 2097152:
            retVal = str(int(bytes / 1048576))+Lang('MB')
        elif bytes >= 2048:
            retVal = str(int(bytes / 1024))+Lang('KB')
        else:
            retVal = str(int(bytes))

        return retVal
