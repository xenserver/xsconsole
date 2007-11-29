
import os, re, sys, time

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
        
        try:
            session.login_with_password(username, password)

        except XenAPI.Failure, e:
            if e.details[0] == 'HOST_IS_SLAVE': # This host is a slave so authenticate with the master
                masterIP = e.details[1] # Master IP is returned in details[1]
                session = XenAPI.Session("http://"+masterIP)
                session.login_with_password(username, password)
            else:
                raise # If the exception is not HOST_IS_SLAVE, raise it again

        return session
    
    def ProcessLogin(self, inUsername, inPassword):
        self.isAuthenticated = False
    
        session= self.TCPSession(inPassword, inUsername)

        # No exception implies a successful login
        self.CloseSession(session)
        self.loggedInUsername = inUsername
        if self.testingHost is not None:
            # Store password when testing only
            self.loggedInPassword = inPassword
        self.authTimestampSeconds = time.time()
        self.isAuthenticated = True
        
    def IsAuthenticated(self):
        if self.isAuthenticated and self.AuthAge() <= State.Inst().AuthTimeoutSeconds():
            retVal = True
        elif State.Inst().IsRecoveryMode():
            retVal = True
        else:
            retVal = False
        return retVal
    
    def AssertAuthenticated(self):
        if not State.Inst().IsRecoveryMode():
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

    def TimeoutSecondsSet(self, inSeconds):
        Auth.Inst().AssertAuthenticated()
        State.Inst().AuthTimeoutSecondsSet(inSeconds)
