# Copyright (c) Citrix Systems 2007. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

from XSConsoleAuth import *
from XSConsoleBases import *
from XSConsoleHotData import *

class TaskEntry:
    def __init__(self, inOpaqueRef, inSession):
        self.opaqueRef = inOpaqueRef
        self.session = inSession
        self.startTime = time.time()
        
    def Status(self):
        retVal = self.session.xenapi.task.get_status(self.opaqueRef.OpaqueRef())
        return retVal
    
    def IsPending(self):
        if self.Status().lower().startswith('pending'):
            retVal = True
        else:
            retVal = False
        return retVal

    def ProgressValue(self):
        retVal = self.session.xenapi.task.get_progress(self.opaqueRef.OpaqueRef())
        return retVal
    
    def DurationSecs(self):
        finished = TimeUtils.DateTimeToSecs(self.session.xenapi.task.get_finished(self.opaqueRef.OpaqueRef()))
        if finished > 0:
            created = TimeUtils.DateTimeToSecs(self.session.xenapi.task.get_created(self.opaqueRef.OpaqueRef()))
            retVal = finished - created
        else:
            retVal = time.time() - self.startTime
        return retVal
    
class Task:
    instance = None
    def __init__(self):
        self.taskList = {}
            
    @classmethod
    def Inst(cls):
        if cls.instance is None:
            cls.instance = Task()
        return cls.instance
    
    def Create(self, inProc):
        session = None
        try:
            session = Auth.Inst().NewSession()
            taskRef = inProc(session)
        except:
            if session is not None:
                Auth.Inst().CloseSession(session)
            raise
        
        hotTaskRef = HotOpaqueRef(taskRef, 'task')
        taskEntry = TaskEntry(hotTaskRef, session)
        self.taskList[hotTaskRef] = taskEntry
        return taskEntry

    @classmethod
    def New(cls, inProc):
        return cls.Inst().Create(inProc)
    
    
