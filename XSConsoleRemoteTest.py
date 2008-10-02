# Copyright (c) Citrix Systems 2008. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

import os, socket, xmlrpclib

from XSConsoleBases import *
from XSConsoleImporter import *
from XSConsoleLang import *
from XSConsoleLog import *
from XSConsoleLayout import *

import SocketServer
import SimpleXMLRPCServer

class UDSXMLRPCServer(SocketServer.UnixStreamServer, SimpleXMLRPCServer.SimpleXMLRPCDispatcher):
    def __init__(self, inAddr, inRequestHandler = None):
        self.logRequests = False
        SimpleXMLRPCServer.SimpleXMLRPCDispatcher.__init__(self)
        SocketServer.UnixStreamServer.__init__(self, inAddr,
            FirstValue(inRequestHandler, SimpleXMLRPCServer.SimpleXMLRPCRequestHandler))
        
    def handle_request(self):
        # Same as base class, but returns True if a request was handled
        try:
            request, client_address = self.get_request()
        except socket.error:
            return False
        if self.verify_request(request, client_address):
            try:
                self.process_request(request, client_address)
            except:
                self.handle_error(request, client_address)
                self.close_request(request)
        return True

class XMLRPCRemoteTest:
    LOCAL_SOCKET_PATH = '/var/xapi/xmlrpcsocket.xsconsole'
    
    def __init__(self):
        if os.path.exists(self.LOCAL_SOCKET_PATH):
            os.unlink(self.LOCAL_SOCKET_PATH)
        self.server = UDSXMLRPCServer(self.LOCAL_SOCKET_PATH)
        self.server.register_introspection_functions()
        for name in dir(self):
            match = re.match(r'HandleXMLRPC(.+)', name)
            if match:
                self.server.register_function(getattr(self, name), match.group(1).lower())
        
        self.SetSocketTimeout(0.0)
        self.ResetStrings()
        Language.SetStringHook(self.StringHook)
        Language.SetErrorHook(self.ErrorHook)

    def SetSocketTimeout(self, inTimeout):        
        self.server.socket.settimeout(inTimeout)

    def ResetStrings(self):
        self.strings = []
        self.errors = []
        self.params = []

    def StringHook(self, inString):
        self.strings.append(inString)

    def ErrorHook(self, inString):
        self.errors.append(inString)

    def SetApp(self, inApp):
        self.app = inApp

    def Poll(self):
        retVal = self.server.handle_request() # True if the server handled a request, False if timed out
        
        # The socket timeout is different for:
        # 1.  XMLRPC idle, where the wait mustn't delay real keypress handling.
        # 2.  Ongoing XML test, where the wait must allow time for the next XML command to arrive
        #   before allowing the next one-second wait for a real keypress, to avoid delays in the test.
        if retVal:
            self.SetSocketTimeout(1.0)
        else:
            self.SetSocketTimeout(0.0)
        return retVal

    def ErrorString(self, inException = None):
        retVal = time.strftime("%Y%m%d%H%M%S", time.gmtime())+'Z ********* Exception *********'
        # The log contains every string translated via Lang, so is verbose and disabled for normal use
        # retVal += "\n\nLog\n\n" + "\n".join(self.strings)
        retVal += "\n\nSnapshot\n\n"
        try:
            snapshot = Layout.Inst().TopDialogue().Snapshot()
            for i, pane in enumerate(snapshot):
                for line in pane:
                    retVal += 'Pane '+str(i) + ':' + line + '\n'
        except Exception, e:
            retVal += 'Failed: '+Lang(e)
        if len(self.errors) > 0:
            retVal += "\n\nExceptions process by Lang()\n\n" + "\n".join(self.errors)
        retVal += "\n\n**************************************\n\nThe command\n\n"
        retVal +=  ":".join(self.params) + "\n\nfailed with:\n\n"
        if inException is not None:
            retVal += Lang(inException)+"\n\n"
        return retVal

    def WrapProcedure(self, inProc): # Any return value of inProc is discarded
        try:
            inProc()
        except Exception, e:
            raise xmlrpclib.Fault(1, self.ErrorString(e))
        return None

    def WrapFunction(self, inFunc): # inFunc returns a value
        try:
            retVal = inFunc()
        except Exception, e:
            raise xmlrpclib.Fault(1, self.ErrorString(e))
        return retVal

    def StandardReturn(self, inInfix = None):
        retVal = time.strftime("%Y%m%d%H%M%S", time.gmtime())+'Z '
        retVal += ':'.join(self.params)
        if inInfix is not None:
            retVal += ' ' + inInfix
        retVal +='  -> OK'
        return retVal

    def HandleXMLRPCNew(self, inTestname):
        """Function: new(<test name>)
        
        Clears current dialogues and resets xsconsole to the first menu item in the root
        menu.  Requires a test name as a parameter, and returns a banner suitable for
        logging.
        """
        self.ResetStrings()
        self.params = ['new', inTestname]
        self.testname = inTestname
        self.WrapProcedure(lambda: Layout.Inst().Reset())
        data = Data.Inst()
        retVal = "\nTest:          "+inTestname
        retVal += "\nHost Version:  "+data.derived.fullversion()
        retVal += "\nHostname:      "+data.host.hostname()
        retVal += "\nManufacturer:  "+data.dmi.system_manufacturer()
        retVal += "\nProduct Name:  "+data.dmi.system_product_name()
        retVal += "\nManagement IP: "+data.ManagementIP()
        retVal += "\n"+self.StandardReturn()
        return retVal
        
    def HandleXMLRPCKeypress(self, inKeypress):
        """Function: keypress(<key name>)
        
        Simulates a keypress.  The parameter should be the ncurses name of a single key,
        e.g. one of 'H', 'KEY_ESCAPE', 'KEY_ENTER', 'KEY_UP', 'KEY_F(8)' or similar
        
        Return a string suitable for logging.
        """
        
        self.params = ['keypress', inKeypress]
        if self.WrapFunction(lambda: self.app.HandleKeypress(inKeypress)):
            retVal = self.StandardReturn()
        else:
            retVal = self.StandardReturn('(keypress ignored)')
        return retVal

    def HandleXMLRPCVerify(self, inString):
        """Function: verify(<search regexp>)
        
        Searches for the input regexp in the log of every string passed to Lang during
        this test.  Raises an exception if not found.  Prefer assertsuccess/assertfail
        to this function if possible.'
        """
        
        self.params = ['verify', inString]
        result = None
        regExp = re.compile(inString)
        for line in self.strings:
            if regExp.match(line):
                result = line
                break
        if result is None:
            raise xmlrpclib.Fault(1, self.ErrorString()+"\n\nSearch string '"+inString+"' not found.")
        return self.StandardReturn("found '"+result+"'")

    def HandleXMLRPCActivate(self, inName):
        """ Function: activate(<plug in name>)
        
        Activates a plug in feature, as if the menu item had been selected from
        the menu.  The same thing can be achieved by sending keypresses of arrow
        keys and enter, but this method avoids dependence on the ordering of items
        within menus.
        
        The name parameter should match the name passed to Importer.RegisterNamedPlugIn
        by the intended plug in.  Returns a string suitable for logging.
        """
        self.params = ['activate', inName]
        self.WrapProcedure(lambda: Importer.ActivateNamedPlugIn(inName))
        return self.StandardReturn()

    def HandleXMLRPCAuthenticate(self, inPassword):
        """Function: authenticate(<password>)
        
        Authenticates within xsconsole, as if the user had entered the password in
        the login dialogue.  Returns a string suitable for logging.
        """
        self.params = ['authenticate', '*' * len(inPassword)]

        self.WrapProcedure(lambda: Auth.Inst().ProcessLogin('root', inPassword))
        return self.StandardReturn()

    def HandleXMLRPCGetData(self):
        """Function: getdata
        
        Returns xsconsole's internal cache of xapi data.
        """
        self.params = ['getdata']
        self.WrapProcedure(lambda: Data.Inst().Update())
        retVal = str(Data.Inst().DataCache())
        return retVal

    def HandleXMLRPCSnapshot(self):
        """Function: snapshot
        
        Returns the contents of the foreground pane(s) on xsconsole's terminal,
        as a list of lists of strings.
        """
        self.params = ['snapshot']
        retVal = self.WrapFunction(lambda: Layout.Inst().TopDialogue().Snapshot())
        return retVal

    def HandleXMLRPCAssertFailure(self):
        """Function: assertfailure
        
        Raises an exception if all operations since the start of the test have
        succeeded.  Otherwise returns a string suitable for logging.
        """
        self.params = ['assertfailure']
        if len(self.errors) == 0:
            raise xmlrpclib.Fault(1, self.ErrorString())
        return self.StandardReturn()
    
    def HandleXMLRPCAssertSuccess(self):
        """Function: assertsuccess
        
        Raises an exception if any of the operations since the start of the test have
        failed.  Otherwise returns a string suitable for logging.
        """
        self.params = ['assertsuccess']
        if len(self.errors) > 0:
            raise xmlrpclib.Fault(1, self.ErrorString())
        return self.StandardReturn()

class NullRemoteTest:
    def __init__(*inParams):
        pass
        
    def Poll(self):
        return False
        
    def SetApp(self, *inParams):
        pass
    
class RemoteTest:
    __instance = None
    
    @classmethod
    def Inst(cls):
        if cls.__instance is None:
            if os.path.exists('/etc/xsconsole/activatexmlrpc'):
                cls.__instance = XMLRPCRemoteTest()
                XSLog('xsconsole XMLRPC interface activated')
            else:
                cls.__instance = NullRemoteTest()
            
        return cls.__instance
