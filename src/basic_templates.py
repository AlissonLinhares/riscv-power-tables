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

import random
import numpy

class TypeU(InstGenerator):
    def _add_random_instruction(self):
        return "        %s %s, %d\n" % (self.instruction,
                                random.choice((self.srcReg + self.dstReg)[1:]),
                                random.randint(0, 2 ** 20 - 1))

# opcode rs2 rs1 opcode rd opcode
class TypeR(InstGenerator):
    def _add_random_instruction(self):
        return "        %s %s, %s, %s\n" % (self.instruction,
                                            random.choice(self.dstReg),
                                            random.choice(self.srcReg),
                                            random.choice(self.srcReg))

# opcode rs2 rs1 opcode rd opcode
class TypeRD(TypeR):
    def init_registers(self):
        # div 0, 0 is not allowed
        self.srcReg.pop(0)

        for r in self.srcReg:
            value = random.randint(0, 2 ** 32 - 1)
            self.program += "        lui " + r + ", %hi(" + str(value) + ")\n"
            self.program += "        addi " + r + ", " + r + ", %lo(" + str(value) + ")\n"

# opcode shamt rs1 opcode rd opcode
class TypeRS(InstGenerator):
    def _add_random_instruction(self):
        return "        %s %s, %s, %d\n" % (self.instruction,
                                            random.choice(self.dstReg),
                                            random.choice(self.srcReg),
                                            random.randint(0, 31))

# imm[11:0] rs1 opcode rd opcode
class TypeI(InstGenerator):
    def _add_random_instruction(self):
        return "        %s %s, %s, %d\n" % (self.instruction,
                                            random.choice(self.dstReg),
                                            random.choice(self.srcReg),
                                            random.randint(0, 2047))

class TypeR4(InstGenerator):
    def _add_random_instruction(self):
        return "        %s %s, %s, %s, %s\n" % (self.instruction,
                                                random.choice(self.dstReg),
                                                random.choice(self.srcReg),
                                                random.choice(self.srcReg),
                                                random.choice(self.srcReg))

class TypeR2(InstGenerator):
    def _add_random_instruction(self):
        return "        %s %s, %s\n" % (self.instruction,
                                        random.choice(self.dstReg),
                                        random.choice(self.srcReg))

class TypeRF(TypeR):
    def _add_random_instruction(self):
        return "        %s %s, %s, %s\n" % (self.instruction,
                                   random.choice(self._ALL_VALID_INT_TGTS),
                                   random.choice(self.srcReg + self.dstReg),
                                   random.choice(self.srcReg + self.dstReg))

class TypeR2DI(TypeRF):
    def _add_random_instruction(self):
        return "        %s %s, %s\n" % (self.instruction,
                                   random.choice(self._ALL_VALID_INT_TGTS),
                                   random.choice(self.srcReg + self.dstReg))

class TypeR2DF(TypeR):
    def _add_random_instruction(self):
        return "        %s %s, %s\n" % (self.instruction,
                                   random.choice(self._ALL_VALID_FLOAT_TGTS),
                                   random.choice(self.srcReg + self.dstReg))

class TypeNOP(TypeRF):
    def _add_random_instruction(self):
        return "        %s\n" % (self.instruction)
