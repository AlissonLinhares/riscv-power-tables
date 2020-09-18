#!/usr/bin/python

import bz2
import argparse
import os
import re
import statistics as st

EXPECTED_END_OF_SIMULATION = "assert raddr0 /= \"0000000000000000000111111111\" report \"Correct End of Simulation\"  severity failure;"

class PowerTable(object):
    def __init__(self):
        self.power_table = {}

    def add_data(self, index, instruction, leakage, internal, switching):
        if instruction not in self.power_table:
            self.power_table[instruction] = {}

        if index not in self.power_table[instruction]:
            self.power_table[instruction][index] = (leakage, internal, switching, True)

    def invalidate_data(self, index, instruction):
        if instruction not in self.power_table:
            self.power_table[instruction] = {}

        self.power_table[instruction][index] = (0.0, 0.0, 0.0, False)

    def show_report(self):
        print "Inst\tLeakage\tInternal\tSwitching\tTotal\tStDev\tVariance"
        for key in self.power_table:
            leakage = []
            internal = []
            switching = []
            total = []

            for index in self.power_table[key]:
                data = self.power_table[key][index]
                if data[3]:
                    leakage.append(data[0])
                    internal.append(data[1])
                    switching.append(data[2])
                    total.append(data[0] + data[1] + data[2])

            if len(total) > 0:
                print "%s\t%f\t%f\t%f\t%f\t%f\t%f" % (key, st.median(leakage), st.median(internal), st.median(switching), st.median(total), st.stdev(total), st.variance(total))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'Generate power tables')
    parser.add_argument('-i', '--input', required=True, help='Input directory')
    parser.add_argument('-o', '--output', required=False, help='Output directory')

    args = parser.parse_args()
    dir = args.input

    full_pt = PowerTable()
    init_pt = PowerTable()

    for file in os.listdir(dir):
        if "init" in file:
            pt = init_pt
        else:
            pt = full_pt

        sp_data = file.split("_")
        index = sp_data[0]
        inst_name = sp_data[1]

        if file.endswith(".pwr"):
            with open(dir + "/" + file, "r") as f:
                power_data = f.read().split("\n")[15].split()
                pt.add_data(index, inst_name, float(power_data[1]),
                        float(power_data[2]), float(power_data[3]))
        elif file.endswith(".pwrerr") and os.stat(dir + "/" + file).st_size != 0:
            print ("Error: %s is not empty!")
            pt.invalidate_data(index, inst_name)

        elif file.endswith(".log.bz2"):
            log_file = bz2.BZ2File(dir + "/" + file,"rb")

            if EXPECTED_END_OF_SIMULATION not in log_file.read():
                print ("Error: %s is not a valid simulation result" % (file))
                pt.invalidate_data(index, inst_name)

            log_file.close()

    print ("Test apps")
    full_pt.show_report()
    print ("Init apps")
    init_pt.show_report()

