# Copyright (c) Citrix Systems 2007. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

import re

# Utils that need to access Data must go in XSConsoleDataUtils,
# and XSConsoleData can't use anything in XSConsoleDataUtils without creating
# circular import problems

class ShellUtils:
    @classmethod
    def MakeSafeParam(cls, inParam):
        if not re.match(r'[-A-Za-z0-9/._~:@]*$', inParam):
            raise Exception("Invalid characters in parameter '"+inParam+"'")
        return inParam
