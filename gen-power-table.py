#!/usr/bin/python

import bz2
import argparse
import os
import re
import statistics as st
import numpy as np
import json

EXPECTED_END_OF_SIMULATION = "Correct End of Simulation"

class PowerData(object):
    def __init__(self, leakage, internal, switching, cycles, valid):
        self.leakage = leakage
        self.internal = internal
        self.switching = switching
        self.cycles = cycles
        self.valid = valid

class PowerTable(object):
    def __init__(self, cpu_freq):
        self.power_table = {}
        self.time_per_cycle = np.float128(1.0) / np.float128(cpu_freq)

    def find_entry(self, index, instruction):
        if instruction not in self.power_table:
            self.power_table[instruction] = {}

        if index not in self.power_table[instruction]:
            self.power_table[instruction][index] = PowerData(np.float128(0.0), np.float128(0.0), np.float128(0.0), np.float128(0.0), True)

        return self.power_table[instruction][index]

    def update_power(self, index, instruction, leakage, internal, switching):
        entry = self.find_entry(index, instruction)
        entry.leakage = np.float128(leakage)
        entry.internal = np.float128(internal)
        entry.switching = np.float128(switching)

    def update_cycles(self, index, instruction, cycles):
        entry = self.find_entry(index, instruction)
        entry.cycles = np.float128(cycles)

    def invalidate_data(self, index, instruction):
        entry = self.find_entry(index, instruction)
        entry.valid = False

    def get_energy(self, instruction):
        leakage = []
        internal = []
        switching = []
        total = []

        for index in self.power_table[instruction]:
            data = self.power_table[instruction][index]

            if data.valid:
                t = data.cycles * self.time_per_cycle
                leakage.append(data.leakage * t)
                internal.append(data.internal * t)
                switching.append(data.switching * t)
                total.append((data.leakage + data.internal + data.switching) * t)

        if len(total) > 0:
            return (st.median(leakage), st.median(internal), st.median(switching), st.median(total))
        else:
            return (0.0, 0.0, 0.0, 0.0)

    def show_report(self):
        print ("%15s %15s %15s %15s %15s" % ("Instruction", "Leakage", "Internal", "Switching", "Total"))

        for instruction in self.power_table:
            et = self.get_energy(instruction)
            # print "%s\t%f\t%f\t%f\t%f\t%f\t%f" % (key, st.median(leakage), st.median(internal), st.median(switching), st.median(total), st.stdev(total), st.variance(total))
            print ("%15s %1.14f %1.14f %1.14f %1.14f" % (instruction, et[0], et[1], et[2], et[3]))

def GenEnergyTable(init_pt, full_pt):
    print ("%15s %15s %15s %15s %15s" % ("Instruction", "Leakage", "Internal", "Switching", "Total"))

    energy_table = {}

    for instruction in full_pt.power_table:
        init = init_pt.get_energy(instruction)
        full = full_pt.get_energy(instruction)

        if (init[3] > 0.0 and full[3] > init[3]):
            leakage = full[0] - init[0]
            internal = full[1] - init[1]
            switching = full[2] - init[2]

            print ("%15s %1.14f %1.14f %1.14f %1.14f" % (instruction,
                                                 leakage,
                                                 internal,
                                                 switching,
                                                 full[3] - init[3]))
            energy_table[instruction] = []
            energy_table[instruction].append({
                "leakage": float(leakage),
                "internal": float(internal),
                "switching": float(switching)
            })
        else:
            e = "----------------"
            print ("%15s %15s %15s %15s %15s" % (instruction, e, e, e, e))

    return energy_table

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'Generate power tables')
    parser.add_argument('-i', '--input', required=True, help='Input directory')
    parser.add_argument('-o', '--output', required=False, help='Output file')

    args = parser.parse_args()
    dir = args.input

    full_pt = PowerTable(40000000.0)
    init_pt = PowerTable(40000000.0)

    for file in os.listdir(dir):
        if "init" in file:
            pt = init_pt
        else:
            pt = full_pt

        sp_data = file.split("_")
        if len(sp_data) < 2:
            continue

        index = sp_data[0]
        if "not_taken" in file:
            inst_name = sp_data[3] + "_not_taken"
        else:
            inst_name = sp_data[1]

        with open(dir + "/" + file, "r") as f:
            data = f.read();

            if file.endswith(".error"):
                if len(data) > 0:
                    print ("Error: %s is not empty" % (file))
                    pt.invalidate_data(index, inst_name)

            elif file.endswith(".log"):
                if EXPECTED_END_OF_SIMULATION not in data:
                    print ("Error: %s invalid simulation result" % (file))
                    pt.invalidate_data(index, inst_name)
                else:
                    idx = data.rfind("CLK(") + 4
                    cycles = int(data[idx:idx+8], 16)
                    pt.update_cycles(index, inst_name, cycles)
            elif file.endswith(".txt"):
                power_data = data.split("\n")[15].split()
                pt.update_power(index, inst_name, float(power_data[1]), float(power_data[2]), float(power_data[3]))


    print ("")
    print ("######### Full result #########")
    full_pt.show_report()

    print ("")
    print ("######### Init result #########")
    init_pt.show_report()

    print ("")
    print ("######### Energy result #########")
    data = GenEnergyTable(init_pt, full_pt)
    with open(args.output, 'w') as outfile:
        json.dump(data, outfile)
