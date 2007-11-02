
import os

from XSConsoleBases import *
import XenAPI

class Auth:
    loggedInName = 'root'
    loggedInPassword = ''
    
    if os.path.isfile("password.txt"):
        passwordFile = open("password.txt")
        try:
            loggedInPassword = passwordFile.readline()
        finally:
            passwordFile.close()
    error = ""
    
    @classmethod
    def LoggedInUsername(cls):
        return cls.loggedInName

    @classmethod
    def LoggedInPassword(cls):
        return cls.loggedInPassword
 
    @classmethod
    def ErrorMessage(cls):
        return cls.error
    
    @classmethod
    def ProcessLogin(cls, inUsername, inPassword):
        # Just accept anything
        cls.loggedInName = inUsername
        cls.loggedInPassword = inPassword
        
        session = cls.OpenSession()
        if session is None:
            cls.loggedInName = None
            cls.loggedInPassword = None
            retVal = False
        else:
            cls.CloseSession(session)
            retVal = True
        return retVal
        
    @classmethod
    def IsLoggedIn(cls):
        return cls.loggedInName != None
        
    @classmethod
    def LogOut(cls):
        cls.loggedInName = None
        cls.loggedInPassword = None

    @classmethod
    def OpenSession(cls):
        session = None
        
        try:
            # Try the local session first
            session = XenAPI.xapi_local()
            session.login_with_password('','')
        except Exception,  e:
            session = None
            cls.error = str(e)
            
        if (session is None and Auth.LoggedInUsername() != None and Auth.LoggedInPassword() != None):
            # Local session couldn't connect, so try remote.
            session = XenAPI.Session("http://127.0.0.1")
            try:
                session.login_with_password(cls.LoggedInUsername(), cls.LoggedInPassword())
            except Exception, e:
                session = None
                cls.error = str(e)

                # Test code
                session = XenAPI.Session("http://isis")
                try:
                    session.login_with_password(cls.LoggedInUsername(), cls.LoggedInPassword())
                except Exception, e:
                    session = None
                    cls.error = str(e)
        return session
        
    @classmethod
    def CloseSession(cls, inSession):
        # inSession.logout()
        return None
