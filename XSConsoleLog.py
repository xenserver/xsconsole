# Copyright (c) 2008-2009 Citrix Systems Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 only.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

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
