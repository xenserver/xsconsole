#!/usr/bin/env python

# Copyright (c) Citrix Systems 2007. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

import sys, traceback

from XSConsoleConfig import *
from XSConsoleLang import *
from XSConsoleLog import *
from XSConsoleTerm import *

def main():
    XSLog('Started as ' + ' '.join(sys.argv))
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
        # Add backtrace to log
        try:
            trace = traceback.format_tb(sys.exc_info()[2])
        except:
            trace = ['Traceback not available']
        XSLogFatal(*trace)
        XSLogFatal('*** Exit caused by unhandled exception: ', str(e))
        raise
