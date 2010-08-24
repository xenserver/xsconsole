#!/usr/bin/env python

# Copyright (c) 2007-2009 Citrix Systems Inc.
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
        try:
            app.Enter()
        except Exception, e:
            # it may be that the screen size has changed
            app.AssertScreenSize()
            # if we get here then it was some other problem
            raise

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
