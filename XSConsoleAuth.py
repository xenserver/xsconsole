# Copyright (c) Citrix Systems 2007. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

import os, re, sys, time
import PAM # From PyPAM module

from XSConsoleBases import *
from XSConsoleLang import *
from XSConsoleState import *

import XenAPI

class Auth:
    instance = None
    
    def __init__(self):
        self.isAuthenticated = False
        self.loggedInUsername = ''
        self.loggedInPassword = '' # Testing only
        self.defaultPassword = ''
        self.testingHost = None
        self.authTimestampSeconds = None
        # The testing.txt file is used for testing only
        if os.path.isfile(sys.path[0]+"/testing.txt"):
            testingFile = open(sys.path[0]+"/testing.txt")
            for line in testingFile:
                match = re.match(r'host=(\w+)', line)
                if match:
                    self.testingHost = match.group(1)
                match = re.match(r'password=(\w+)', line)
                if match:
                    self.defaultPassword = match.group(1)

            testingFile.close()

    @classmethod
    def Inst(cls):
        if cls.instance is None:
            cls.instance = Auth()
        return cls.instance
    
    def AuthAge(self):
        if self.isAuthenticated:
            retVal = time.time() - self.authTimestampSeconds
        else:
            raise(Exception, "Cannot get age - not authenticated")
        return retVal
    
    def KeepAlive(self):
        if self.isAuthenticated:
            if self.AuthAge() <= State.Inst().AuthTimeoutSeconds():
                # Auth still valid, so update timestamp to now
                self.authTimestampSeconds = time.time()
    
    def LoggedInUsername(self):
        if (self.isAuthenticated):
            retVal = self.loggedInUsername
        else:
            retVal = None
        return retVal
    
    def DefaultPassword(self):
        return self.defaultPassword
    
    def ErrorMessage(self):
        return self.error
    
    def TCPSession(self, inPassword = None,  inUsername = None):
        username = FirstValue(inUsername, self.loggedInUsername)
        password = inPassword

        # Create a local login if we can
        session = XenAPI.Session("http://"+FirstValue(self.testingHost, "127.0.0.1"))
        isSlave = False
        
        try:
            session.login_with_password(username, password)

        except XenAPI.Failure, e:
            if e.details[0] == 'HOST_IS_SLAVE': # This host is a slave so authenticate with the master
                masterIP = e.details[1] # Master IP is returned in details[1]
                session = XenAPI.Session("http://"+masterIP)
                session.login_with_password(username, password)
                isSlave = True
            else:
                raise # If the exception is not HOST_IS_SLAVE, raise it again

        return session, isSlave
    
    def ProcessLogin(self, inUsername, inPassword):
        self.isAuthenticated = False
        
        if inUsername != 'root':
            raise Exception(Lang("Only root can log in here"))
        
        # Old method via xapi
        # session= self.TCPSession(inPassword, inUsername)

        def PAMConv(inAuth, inQueryList, inUserData):
            retVal = []
            for query in inQueryList:
                if query[1] == PAM.PAM_PROMPT_ECHO_ON or query[1] == PAM.PAM_PROMPT_ECHO_OFF:
                    # Return inPassword from the scope that encloses this function
                    retVal.append((inPassword, 0)) # Append a tuple with two values (so double brackets)
            return retVal
            
        auth = PAM.pam()
        auth.start('passwd')
        auth.set_item(PAM.PAM_USER, inUsername)
        auth.set_item(PAM.PAM_CONV, PAMConv)
        
        auth.authenticate() 
        auth.acct_mgmt()
        
        # No exception implies a successful login
        
        # self.CloseSession(session) # Reuired for old method
        
        self.loggedInUsername = inUsername
        if self.testingHost is not None:
            # Store password when testing only
            self.loggedInPassword = inPassword
        self.authTimestampSeconds = time.time()
        self.isAuthenticated = True
        
    def IsAuthenticated(self):
        if self.isAuthenticated and self.AuthAge() <= State.Inst().AuthTimeoutSeconds():
            retVal = True
        else:
            retVal = False
        return retVal
    
    def AssertAuthenticated(self):
        if not self.isAuthenticated:
            raise Exception("Not logged in")
        if self.AuthAge() > State.Inst().AuthTimeoutSeconds():
            raise Exception("Session has timed out")

    def LogOut(self):
        self.isAuthenticated = False
        self.loggedInUsername = None

    def OpenSession(self):
        session = None
        
        try:
            # Try the local Unix domain socket first
            session = XenAPI.xapi_local()
            session.login_with_password('root','')
        except Exception,  e:
            session = None
            self.error = Lang(e)
            
        if session is None and self.testingHost is not None:
            # Local session couldn't connect, so try remote.
            session = XenAPI.Session("http://"+self.testingHost)
            try:
                session.login_with_password(self.loggedInUsername, self.loggedInPassword)
                
            except XenAPI.Failure, e:
                if e.details[0] != 'HOST_IS_SLAVE': # Ignore slave errors when testing
                    session = None
                    self.error = Lang(e)
            except Exception, e:
                session = None
                self.error = Lang(e)
        return session
        
    def CloseSession(self, inSession):
        # inSession.logout()
        return None

    def IsPasswordSet(self):
        # Security critical - mustn't wrongly return False
        retVal = True
        
        file = open("/etc/passwd")
        for line in file:
            if re.match(r'root:', line):
                if re.match(r'root:!!:', line):
                    retVal = False
                break # break on any root: line
        file.close()
        return retVal
    
    def ChangePassword(self, inOldPassword, inNewPassword):

        if not self.IsPasswordSet():
            # Write password directly
            pipe = os.popen("/usr/sbin/chpasswd", "w")
            pipe.write("root:"+inNewPassword+"\n")
            pipe.close()
            
            # xlock won't have started if there's no password, so start it now
            if os.path.isfile("/usr/bin/xautolock"):
                commands.getstatusoutput("/usr/bin/xautolock -time 10 -locker '/usr/bin/xlock -mode blank' &")
                # Ignore failures
        else:
            session, isSlave = Auth.Inst().TCPSession(inOldPassword)
            session.xenapi.session.change_password(inOldPassword, inNewPassword)
            if isSlave:
                # Write local password as well
                pipe = os.popen("/usr/sbin/chpasswd", "w")
                pipe.write("root:"+inNewPassword+"\n")
                pipe.close()
            
        # Caller handles exceptions
        
    def TimeoutSecondsSet(self, inSeconds):
        Auth.Inst().AssertAuthenticated()
        State.Inst().AuthTimeoutSecondsSet(inSeconds)
