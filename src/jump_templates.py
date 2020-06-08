# Copyright (C) 2020 Alisson Linhares, Rodolfo Azevedo.
# All rights reserved.
#
# This project is a free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This file is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details:
#
# <http://www.gnu.org/licenses/>.

from src.default_template import InstGenerator

import numpy
import random
import statistics

class TypeJ(InstGenerator):
    def __init__(self, instruction, format):
        InstGenerator.__init__(self, instruction, format)
        self.jump_table = []

    def __gen_jump_table(self, nInstructions):
        addr_table = random.sample(range(1, nInstructions - 1), nInstructions - 2)
        addr_table.append(nInstructions - 1)

        jump_table = numpy.empty(nInstructions,  dtype=object)

        curr = 0
        for jmp in addr_table:
            jump_table[curr] = self._build_instruction(str(curr), str(jmp))
            curr = jmp

        jump_table[nInstructions-1] = ".label" + str(curr) + ":\n"
        return jump_table.tolist()

    def generate_program(self, iterations, nInstructions):
        self.jump_table = self.__gen_jump_table(nInstructions)
        super(TypeJ, self).generate_program(iterations, nInstructions)

    def _build_instruction(self, id, addr):
        return ".label%s:\n        %s %s, .label%s\n" % (id,
                                                 self.instruction,
                                                 random.choice(self.srcReg),
                                                 addr)

    def init_registers(self):
        for r in self.srcReg[1:]:
            self.program += "        li %s, %d\n" % (r, 0)

    def _add_random_instruction(self):
        return self.jump_table.pop(0)

class TypeJR(TypeJ):
    def init_registers(self):
        for r in self.srcReg[1:]:
            self.program += "        la %s, .loop\n" % (r)

    def _build_instruction(self, id, addr):
        addr = str(int(addr) * 4);
        return ".label%s:\n         %s  %s, %s, %s\n" % (id,
                                                 self.instruction,
                                                 random.choice(self.dstReg),
                                                 random.choice(self.srcReg[1:]),
                                                 addr)

class TypeB(TypeJ):
    EQUAL_TST  = 0
    GRATER_TST = 1
    LOWER_TST  = 2

    def __init__(self, instruction, format, cmp_method, prefix = ""):
        InstGenerator.__init__(self, instruction, format)
        self.init_list = ""
        self.prefix = prefix
        self.cmp_method = cmp_method
        self.seed = random.randint(0, 2 ** 20 - 1)
        self.samples = [random.randint(1, 2 ** 20 - 1) for i in range(0, len(self.srcReg))]
        random.shuffle(self.samples)
        self.median = statistics.median(self.samples)
        self.lower_list = ["x0"]
        self.grater_list = []

        if self.cmp_method == TypeB.EQUAL_TST:
            for r in self.srcReg[1:]:
                self.init_list += "        li %s, %d\n" % (r, self.seed)
        else:
            for r in self.srcReg[1:]:
                value = self.samples.pop()

                if value > self.median:
                    self.grater_list.append(r)
                else:
                    self.lower_list.append(r)

                self.init_list += "        li %s, %d\n" % (r, value)

    def init_registers(self):
        self.program += self.init_list

    def _build_instruction(self, id, addr):
        if self.cmp_method == TypeB.EQUAL_TST:
            return ".label%s:\n        %s %s, %s, .label%s\n" % (id,
                                            self.instruction,
                                            random.choice(self.srcReg[1:]),
                                            random.choice(self.srcReg[1:]),
                                            addr)

        elif self.cmp_method == TypeB.LOWER_TST:
            return ".label%s:\n        %s %s, %s, .label%s\n" % (id,
                                            self.instruction,
                                            random.choice(self.lower_list),
                                            random.choice(self.grater_list),
                                            addr)

        return ".label%s:\n        %s %s, %s, .label%s\n" % (id,
                                            self.instruction,
                                            random.choice(self.grater_list),
                                            random.choice(self.lower_list),
                                            addr)
