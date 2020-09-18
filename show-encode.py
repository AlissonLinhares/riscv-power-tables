#!/usr/bin/python

import subprocess
import os
import sys

if __name__ == '__main__':
    if len(sys.argv) <= 1:
        print ("File not found.")
        exit(0)

    with open(sys.argv[1], "r") as file:
        dados = file.read().split("\n")
        for inst in dados:
            subprocess.call('echo "DASM(0x%s)" | spike-dasm' % inst[8:16], shell=True)
            subprocess.call('echo "DASM(0x%s)" | spike-dasm' % inst[0:8] , shell=True)

            if inst == "0000000000000000":
                exit(0)
