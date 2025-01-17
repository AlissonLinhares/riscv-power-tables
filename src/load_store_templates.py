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

# imm[11:0] rs1 opcode rd opcode
class TypeILS(InstGenerator):
    def __init__(self, instruction, format, baseAddress, endAddress):
        InstGenerator.__init__(self, instruction, format)
        self.baseAddress = baseAddress
        self.endAddress = endAddress

    def _get_base_addr(self):
        addr = random.randint(self.baseAddress + 2048, self.endAddress - 2048)
        return (addr >> 3) << 3

    def _get_offset(self):
        return random.randint(1, 256) * 8 - 8

    def init_registers(self):
        for r in self.srcReg[1:]:
            value = self._get_base_addr()
            self.program += "        lui " + r + ", %hi(" + str(value) + ")\n"
            self.program += "        addi " + r + ", " + r + ", %lo(" + str(value) + ")\n"

    def _add_random_instruction(self):
        return "        %s %s, %d(%s)\n" % (self.instruction,
                                            random.choice(self.dstReg),
                                            self._get_offset(),
                                            random.choice(self.srcReg[1:]))

class TypeILSF(TypeILS):
    def init_registers(self):
        super(TypeILS, self).init_registers()

        for r in self._ALL_VALID_INT_TGTS:
            value = self._get_base_addr()
            self.program += "        lui " + r + ", %hi(" + str(value) + ")\n"
            self.program += "        addi " + r + ", " + r + ", %lo(" + str(value) + ")\n"

    def _add_random_instruction(self):
        return "        %s %s, %d(%s)\n" % (self.instruction,
                                            random.choice(self._ALL_VALID_FLOAT_TGTS),
                                            self._get_offset(),
                                            random.choice(self._ALL_VALID_INT_TGTS))
