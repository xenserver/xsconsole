# Copyright (c) Citrix Systems 2008. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

import syslog
from XSConsoleBases import *
from XSConsoleLang import *

def XSLog(*inParams):
    XSLogger.Inst().Log(syslog.LOG_INFO, *inParams)
    
def XSLogFatal(*inParams):
    XSLogger.Inst().Log(syslog.LOG_CRIT, *inParams)

# XSLogFailure should be used for errors implying a test failure.  Otherwise use XSLogError
def XSLogError(*inParams):
    XSLogger.Inst().Log(syslog.LOG_ERR, *inParams)

def XSLogFailure(*inParams):
    XSLogger.Inst().LogFailure(*inParams)

class XSLogger:
    __instance = None

    def __init__(self):
        syslog.openlog('xsconsole')

    @classmethod
    def Inst(cls):
        if cls.__instance is None:
            cls.__instance = XSLogger()
        return cls.__instance

    def Log(self, inPriority, *inParams):
        for param in inParams:
            syslog.syslog(inPriority, str(param))
            
    def LogFailure(self, *inParams):
        logString = "\n".join( [ str(param) for param in inParams ] )
        message = Lang(Exception(logString)) # Translation using Lang() causes the exception tp be logged

    def ErrorLoggingHook(self, *inParams):
        # This hook is called by Lang(Exception), so mustn't call Lang(Exception) itself
        logString = "\n".join( [ str(param) for param in inParams ] )
        self.Log(syslog.LOG_ERR, 'Exception: '+logString)

Language.SetErrorLoggingHook(XSLogger.Inst().ErrorLoggingHook)
