#!/usr/bin/python3

# ----------------------------------------------------------------------------------------
# RNPS aka Rapid Network Port Scan
# Copyright (C) 2022 Ivan Maruca <ivan>DOT<maruca>AT<gmail>DOT<com>
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see https://www.gnu.org/licenses/agpl-3.0.en.html
# ----------------------------------------------------------------------------------------

import signal
import sys
from time import sleep
from rnps.output import Output
from rnps.validator import Validator

loadingCounter = 0

def loading():
    global loadingCounter
    bar = [
        " [■     ]",
        " [■■    ]",
        " [■■■   ]",
        " [■■■■  ]",
        " [■■■■■ ]",
        " [■■■■■■]",
        " [ ■■■■■]",
        " [  ■■■■]",
        " [   ■■■]",
        " [    ■■]",
        " [     ■]",
        " [      ]",
    ]
    print(bar[loadingCounter % len(bar)], end="\r")
    sleep(.2)
    loadingCounter += 1

def abort(f,s):
    print("Aborting...")
    exit()

def main():
    signal.signal(signal.SIGINT,abort)
    try:
        val = Validator()
        out = Output(val)
        errs = val.validate()
        if len(errs) > 0:
            for e in errs:
                print("{}".format(e))
            exit()
        sys.stdout.write(out.header())
        scan = val.getScan()
        scan.start()
        while scan.is_alive():
            loading()

        out.setResult(scan.result())
        out.send()
    except:
        pass

if __name__ == "__main__":
    main()