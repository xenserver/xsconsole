# Copyright (c) Citrix Systems 2007. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

import os, popen2, sys
from pprint import pprint

from XSConsoleBases import *

oldPath = sys.path
sys.path = ['/opt/xensource/sm'] + sys.path
if os.path.isfile(sys.path[0]+'/shared_db_util.py'):
    try:
        import shared_db_util
    except Exception, e:
        print "Exception importing shared_db_util.py: " + str(e)
        # Ignore
sys.path = oldPath

class RemoteDB:
    instance = None
    
    @classmethod
    def Inst(cls):
        if cls.instance is None:
            cls.instance = RemoteDB()
        return cls.instance
    
    def ReadConf(self):
        retVal = shared_db_util.read_remote_db_conf()
        return retVal
        
    def LocalIQN(self):
        # Try using the XenAPI first if xapi is running
        if shared_db_util.is_xapi_running():
            try:
                retVal = shared_db_util.get_local_iqn_from_xapi()
                if retVal <> '':
                    return retVal
            except:
                pass 
        # Otherwise use the database read tool
        retVal = shared_db_util.get_local_iqn(False) # Try local conf file
        if retVal == '':
            retVal = shared_db_util.get_local_iqn(True) # Try remote conf file
        return retVal
    
    def ProbeIQNs(self, inParams):
        probedIQNs = shared_db_util.probe_iqns(
            inParams.get('localiqn', self.LocalIQN()),
            inParams['remotehost'],
            int(inParams.get('port', 3260)),
            inParams.get('username', ''),
            inParams.get('password', '')
        )
            
        retVal = []
        for iqn in probedIQNs:
            retVal.append(Struct(portal = iqn[0], tpgt=iqn[1], name=iqn[2]))
            
        return retVal
    
    def ProbeLUNs(self, inParams, inIQN):
        target, port = inIQN.portal.split(':')
        probedLUNs = shared_db_util.probe_luns(
            inParams.get('localiqn', self.LocalIQN()),
            target,
            int(port),
            inParams.get('username', ''),
            inParams.get('password', ''),
            inIQN.name
        )
        
        return probedLUNs

    def TestLUN(self, inParams, inIQN, inLUN):
        target, port = inIQN.portal.split(':')
        retVal = shared_db_util.test(
            inParams.get('localiqn', self.LocalIQN()),
            target,
            int(port),
            inParams.get('username', ''),
            inParams.get('password', ''),
            inIQN.name,
            inLUN
        )
        return retVal
        
    def FormatLUN(self, inParams, inIQN, inLUN):
        target, port = inIQN.portal.split(':')
        retVal = shared_db_util.format(
            inParams.get('localiqn', self.LocalIQN()),
            target,
            int(port),
            inParams.get('username', ''),
            inParams.get('password', ''),
            inIQN.name,
            inLUN
        )
        return retVal

    def ReadyForUse(self, inParams, inIQN, inLUN):
        target, port = inIQN.portal.split(':')
        # Prevent script failure by writing this first
        shared_db_util.write_remote_db_conf(
            inParams.get('localiqn', self.LocalIQN()),
            target,
            int(port),
            inParams.get('username', ''),
            inParams.get('password', ''),
            inIQN.name,
            inLUN
        )        
        retVal = shared_db_util.ready_for_use(
            inParams.get('localiqn', self.LocalIQN()),
            target,
            int(port),
            inParams.get('username', ''),
            inParams.get('password', ''),
            inIQN.name,
            inLUN
        )
        return retVal

    def ConfigureNoDB(self):
        confCommands = [
            '(export TERM=xterm && /etc/init.d/xs-remote-db stop)',
            '/bin/rm /etc/xensource/remote.db.conf',
            '/bin/cp -pf /etc/xensource/local.db.conf /etc/xensource/db.conf'
            ]
            
        for command in confCommands:
                    
            popenObj = popen2.Popen4(command)
            popenObj.tochild.close() # Send EOF
            
            # This method avoids the Interrupted System Call exception
            while True:
                try:
                    popenObj.wait() # Must wait for completion
                    break
                except IOError, e:
                    if e.errno != errno.EINTR: # Loop if EINTR
                        raise
                
