
import re

# Utils that need to access Data must go in DataUtils,
# and XSConsoleData can't use anything in here

class ShellUtils:
    @classmethod
    def MakeSafeParam(cls, inParam):
        if not re.match(r'[-A-Za-z0-9/._~:]*$', inParam):
            raise Exception("Invalid characters in parameter '"+inParam+"'")
        return inParam
