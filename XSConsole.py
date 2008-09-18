#!/usr/bin/env python

# Copyright (c) Citrix Systems 2007. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

import sys

from XSConsoleConfig import *
from XSConsoleTerm import *
from XSConsoleLang import *

def main():
    if '--shelltimeout' in sys.argv:
        # Print a shell timeout value, suitable for TMOUT=`xsconsole --shelltimeout`
        if Config.Inst().AllShellsTimeout():
            print State.Inst().AuthTimeoutSeconds()
        else:
            print
    else:
        app = App.Inst()
        app.Build( ['plugins-base', 'plugins-oem', 'plugins-extras'] )
        app.Enter()

if __name__ == "__main__":
    try:
        main()
    except Exception, e:
        print Lang(e)
        raise
