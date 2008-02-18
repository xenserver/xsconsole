# Copyright (c) Citrix Systems 2007. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

import re, signal

# Utils that need to access Data must go in XSConsoleDataUtils,
# and XSConsoleData can't use anything in XSConsoleDataUtils without creating
# circular import problems

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
                inPipe.wait() # Must wait for completion before mkfs
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
            
