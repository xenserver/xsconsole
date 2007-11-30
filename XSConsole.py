#!/usr/bin/env python

# Copyright (c) Citrix Systems 2007. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

import sys

from XSConsoleTerm import *
from XSConsoleLang import *

def main():
    app = App()
    app.Enter()

if __name__ == "__main__":
    try:
        main()
    except Exception, e:
        print Lang(e)
        raise
