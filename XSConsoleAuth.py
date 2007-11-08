
import os, re

from XSConsoleBases import *
import XenAPI

class Auth:
    instance = None
    
    def __init__(self):
        self.isAuthenticated = False
        self.loggedInUsername = ''
        self.loggedInPassword = '' # Testing only
        self.defaultPassword = ''
        self.testingHost = None
        # The testing.txt file is used for testing only
        if os.path.isfile("testing.txt"):
            testingFile = open("testing.txt")
            for line in testingFile:
                match = re.match(r'host=(\w+)', line)
                if match: self.testingHost = match.group(1)
                match = re.match(r'password=(\w+)', line)
                if match: self.defaultPassword = match.group(1)

            testingFile.close()

    @classmethod
    def Inst(cls):
        if cls.instance is None:
            cls.instance = Auth()
        return cls.instance
    
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
    
    def ProcessLogin(self, inUsername, inPassword):
        self.isAuthenticated = False
    
        # Create a local login if we can
        session = XenAPI.Session("http://"+FirstValue(self.testingHost, "127.0.0.1"))
        try:
            session.login_with_password(inUsername, inPassword)

        except Exception, e:
            # Should check for slave response here
            session = None
            self.error = str(e)

        if session is None:
            retVal = False
        else:
            # Successful login
            self.CloseSession(session)
            self.loggedInUsername = inUsername
            if self.testingHost is not None:
                # Store password when testing only
                self.loggedInPassword = inPassword
            self.isAuthenticated = True
            retVal = True
        return retVal
        
    def IsAuthenticated(self):
        return self.isAuthenticated
        
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
            self.error = str(e)
            
        if session is None and self.testingHost is not None:
            # Local session couldn't connect, so try remote.
            session = XenAPI.Session("http://"+self.testingHost)
            try:
                session.login_with_password(self.loggedInUsername, self.loggedInPassword)
            except Exception, e:
                session = None
                self.error = str(e)
        return session
        
    def CloseSession(self, inSession):
        # inSession.logout()
        return None
