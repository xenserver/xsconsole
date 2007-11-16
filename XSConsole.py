#!/usr/bin/env python

import sys
from XSConsoleTerm import *

def main():
    app = App()
    app.Enter()

if __name__ == "__main__":
    try:
        main()
    except Exception, e:
        print str(e)
        raise
