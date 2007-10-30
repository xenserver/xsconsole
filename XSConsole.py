#!/usr/bin/env python

import sys
from XSConsoleTerm import *

def main():
    app = App()
    app.Enter()

if __name__ == "__main__":
    print "Starting..."
    try:
        main()
    except Exception, e:
        print str(e)
        raise
    print >> sys.stderr, "Done."
