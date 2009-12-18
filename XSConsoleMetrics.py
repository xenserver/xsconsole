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

import XenAPI
import urllib
import xml.dom.minidom

from XSConsoleAuth import *
from XSConsoleBases import *
from XSConsoleLang import *

class HotMetrics:
    LIFETIME_SECS = 5 # The lifetime of objects in the cache before they are refetched
    SNAPSHOT_SECS = 10 # The number of seconds of metric data to fetch
    __instance = None
    
    @classmethod
    def Inst(cls):
        if cls.__instance is None:
            cls.__instance = HotMetrics()
        return cls.__instance
        
    def __init__(self):
        self.data = {}
        self.timestamp = None
        self.thisHostUUID = None
        
    def LocalHostMetrics(self):
        self.UpdateMetrics()
        retVal = {}
        hostPrefix = r'AVERAGE:host:'+self.thisHostUUID
        cpuRE = re.compile(hostPrefix+r':cpu[0-9]+')
        cpuValues = [ float(v) for k, v in self.data.iteritems() if cpuRE.match(k) ]
        retVal['numcpus'] = len(cpuValues)
        if len(cpuValues) == 0:
            retVal['cpuusage'] = None
        else:
            retVal['cpuusage'] = sum(cpuValues) / len(cpuValues)
        
        try:
            retVal['memory_total'] = float(self.data[hostPrefix +':memory_total_kib']) * 1024.0
        except Exception, e:
            retVal['memory_total'] = None
        
        try:
            retVal['memory_free'] = float(self.data[hostPrefix +':memory_free_kib']) * 1024.0
        except Exception, e:
            retVal['memory_free'] = None

        return retVal

    def VMMetrics(self, inUUID):
        self.UpdateMetrics()
        retVal = {}
        vmPrefix = r'AVERAGE:vm:' + inUUID

        cpuRE = re.compile(vmPrefix+r':cpu[0-9]+')
        cpuValues = [ float(v) for k, v in self.data.iteritems() if cpuRE.match(k) ]
        retVal['numcpus'] = len(cpuValues)
        if len(cpuValues) == 0:
            retVal['cpuusage'] = None
        else:
            retVal['cpuusage'] = sum(cpuValues) / len(cpuValues)

        try:
            retVal['memory_total'] = float(self.data[vmPrefix +':memory']) # Not scaled
        except Exception, e:
            retVal['memory_total'] = None
        
        try:
            retVal['memory_free'] = float(self.data[vmPrefix +':memory_internal_free']) * 1024.0 # Value is in kiB
        except Exception, e:
            retVal['memory_free'] = None

        return retVal

    def UpdateMetrics(self):
        timeNow = time.time()
        if self.timestamp is None or abs(timeNow - self.timestamp) > self.LIFETIME_SECS:
            # Refetch host metrics
            self.data = self.FetchData()
            self.timestamp = timeNow
        
    def ParseXML(self, inXML):
        xmlDoc = xml.dom.minidom.parseString(inXML)
        metaNode = xmlDoc.getElementsByTagName('meta')[0]
        valuesNode = xmlDoc.getElementsByTagName('data')[0]
        
        meta = Struct()
        # Values comments out below are currently not required
        # for name in ('start', 'end', 'rows', 'columns'):
        #     setattr(meta, name, int(metaNode.getElementsByTagName(name)[0].firstChild.nodeValue.strip()))
        legendNode = metaNode.getElementsByTagName('legend')[0]
        meta.entries = [ str(entry.firstChild.nodeValue.strip()) for entry in legendNode.getElementsByTagName('entry') ]
        
        # Find the most recent row in the values
        mostRecentRow = None
        mostRecentTime = None
        for row in valuesNode.getElementsByTagName('row'):
            rowTime = int(row.getElementsByTagName('t')[0].firstChild.nodeValue.strip())
            if mostRecentTime is None or mostRecentTime < rowTime:
                mostRecentRow = row
                mostRecentTime = rowTime
                
        # Decode the row contents
        if mostRecentRow is None:
            values = []
        else:
            values = [ str(v.firstChild.nodeValue.strip()) for v in mostRecentRow.getElementsByTagName('v') ]
    
        retVal = {}
        for entry, value in zip(meta.entries, values):
            retVal[entry] = value
            
        return retVal

    def FetchData(self):
        retVal = None
        session = Auth.Inst().OpenSession()
        try:
            sessionID = session._session
            if self.thisHostUUID is None:
                # Make use of this session to get the local host UUID
                opaqueRef = session.xenapi.session.get_this_host(sessionID)
                self.thisHostUUID = session.xenapi.host.get_uuid(opaqueRef)
                
            httpRequest = 'https://localhost/rrd_updates?session_id=%s&start=%s&host=true' % (sessionID, int(time.time()) - self.SNAPSHOT_SECS)
            
            socket = urllib.URLopener().open(httpRequest)
            try:
                content = socket.read()
            finally:
                socket.close()
            retVal = self.ParseXML(content)    
                
        finally:
            if session is not None:
                Auth.Inst().CloseSession(session)
        
        return retVal
        
                
