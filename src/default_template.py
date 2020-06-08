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

import random
import string
import os
import numpy
import struct

from enum import Enum

class Extension(Enum):
    I = 0
    S = 1
    D = 2
    X = 3

class InstGenerator(object):
    _templateHeader = """
        .section ".text"
        .globl _start
_start:
        li x1, $iterations
"""

    _templateFooter = """
        addi x1, x1, -1
        bne x1, x0, .loop
        j 0x1FF0
end:    beq x0, x0, end

        .section .rodata
        .align  2
"""

    # Based on Dynamically Exploiting Narrow Width Operands to Improve Processor Power and Performance,
    # David Brooks and Margaret Martonosi, HPCA 99
    _RAND_WEIGHT = [
        0.2222222,  0.1180556,  0.0347222,  0.0486111,  0.0694444,  0.0486111,
        0.0486111,  0.0486111,  0.0486111,  0.0555556,  0.0277778,  0.0277778,
        0.0069444,  0.0138889,  0.0208333,  0.0208333,  0.0208333,  0.0138889,
        0.0138889,  0.0069444,        0.0,  0.0138889,  0.0138889,  0.0277778,
              0.0,  0.0069444,        0.0,        0.0,  0.0069444,  0.0069444,
              0.0,        0.0,    0.006944700000000286
    ] #0.0069444

    _WRANGE = range(0, len(_RAND_WEIGHT))

    _REAL_VALUES = [
        1.0, # one
        0.5, # half
        3.14159265358979323846, # pi
        1.41421356237309504880, # sqr2
        1.73205080756887729352, # sqr3
        0.70710678118654752440, # sqri
        1.61803398874989484820, # phi
        2.71828182845904523536, # eule
        0.69314718055994530941, # ln2
        0.83462684167407318628, # gaus
        4.81047738096535165547, # john
        262537412640768743.999999999999250073, # hermiteRamanuj
        1.75793275661800453270, # kasne
        23.1406926327792690057, # gelfon
        4.53236014182719380962, # vanderpau
        2.50290787509589282228, # feigenbau
        1.5065918849, # mandelbrotAre
        2.39996322972865332223, # goldenAngl
        4.53236014182719380962, # vanDerPau
        0.65028784016, # sin1
        -0.98803162409, # sin3
        0.85090352453, # sin4
        -0.3048106211, # sin6
        -0.38778163541, # sin7
        0.92175126972, # cos7
        0.8939966636, # sin9
        -0.44807361613, # cos9
    ]

    _ALL_VALID_INT_TGTS = [
                               'x2',  'x3',  'x4',  'x5',  'x6',  'x7',  'x8',
                 'x9', 'x10', 'x11', 'x12', 'x13', 'x14', 'x15', 'x16', 'x17',
                'x18', 'x19', 'x20', 'x21', 'x22', 'x23', 'x24', 'x25', 'x26',
                'x27', 'x28', 'x29', 'x30', 'x31'
    ]

    _ALL_VALID_FLOAT_TGTS = [
                'f0',  'f1',  'f2',  'f3',  'f4',  'f5',  'f6',  'f7',  'f8',
                'f9', 'f10', 'f11', 'f12', 'f13', 'f14', 'f15', 'f16', 'f17',
               'f18', 'f19', 'f20', 'f21', 'f22', 'f23', 'f24', 'f25', 'f26',
               'f27', 'f28', 'f29', 'f30', 'f31'
    ]


    def __init__(self, instruction, format = Extension.I):
        self.instruction = instruction
        self.program = ''
        self.dir = 'test-programs'
        self.prefix = ''
        self.format = format
        self.dstReg = []

        if self.format in (Extension.S, Extension.D):
            self.srcReg = [
                'f0',  'f1',  'f2',  'f3',  'f4',  'f5',  'f6',  'f7',  'f8',
                'f9', 'f10', 'f11', 'f12', 'f13', 'f14', 'f15', 'f16', 'f17',
               'f18', 'f19', 'f20', 'f21', 'f22', 'f23', 'f24', 'f25', 'f26',
               'f27', 'f28', 'f29', 'f30', 'f31'
            ]
        else:
            self.srcReg = [
                 'x0',         'x2',  'x3',  'x4',  'x5',  'x6',  'x7',  'x8',
                 'x9', 'x10', 'x11', 'x12', 'x13', 'x14', 'x15', 'x16', 'x17',
                'x18', 'x19', 'x20', 'x21', 'x22', 'x23', 'x24', 'x25', 'x26',
                'x27', 'x28', 'x29', 'x30', 'x31'
            ]

    def init_registers(self):
        registers = self.srcReg + self.dstReg

        if self.format == Extension.S:
            for r in registers:
                label = "." + r +"_DATA"
                self.program += "        lui a5, %hi(" + label + ")\n"
                self.program += "        flw " + r + ", %lo(" + label + ")(a5)\n"
                self.alloc_single_value(random.choice(self._REAL_VALUES), label)
        elif self.format == Extension.D:
            for r in registers:
                label = "." + r +"_DATA"
                self.program += "        lui a5, %hi(" + label + ")\n"
                self.program += "        fld " + r + ", %lo(" + label + ")(a5)\n"
                self.alloc_double_value(random.choice(self._REAL_VALUES), label)
        else:
            for r in registers[1:]:
                value = 2 ** numpy.random.choice(self._WRANGE, p=self._RAND_WEIGHT) - 1
                self.program += "        li %s, %d\n" % (r, value)

    def alloc_single_value(self, value, label):
        result = 0
        bstr = bin(struct.unpack('i',struct.pack('f',value))[0])

        if (value > 0.0):
            result = int(bstr[2::].zfill(32)[0:32],2)
        else:
            result = int(bstr[3::].zfill(32)[0:32],2) or 0x80000000

        self._templateFooter += "%s:\n\
        .word  %d\n\
        .align  2\n" % (label, result)

    def alloc_double_value(self, value, label):
        bstr = bin(struct.unpack('Q',struct.pack('d',value))[0])[2::].zfill(64)
        right = int(bstr[32:64],2)
        left = 0

        if (value > 0.0):
            left = int(bstr[0:32],2)
        else:
            left = int(bstr[0:32],2) or 0x80000000


        self._templateFooter += "%s:\n\
        .word  %d\n\
        .word  %d\n\
        .align  3\n" % (label, right, left)

    def reserve_destination_registers(self, number):
        for i in range(0, number):
            register = random.choice(self.srcReg[1:])
            self.srcReg.remove(register)
            self.dstReg.append(register)

    def _add_random_instruction(self):
        return '# No template given\n'

    def __add_header(self, iterations):
        self.program += string.replace(self._templateHeader, '$iterations', str(iterations))

    def __add_loop_label(self):
        self.program += "\n.loop:\n"

    def __add_footer(self):
        self.program += self._templateFooter

    def __force_alignment(self):
        self.program += '        .align 7'

    def __save_program(self, iterations, nInstructions):
        if not os.path.exists(self.dir):
            os.makedirs(self.dir)

        file_name = os.path.join(self.dir,
                                   self.prefix +
                                   self.instruction +
                                   '_' +
                                   str(iterations) +
                                   'x' +
                                   str(nInstructions) +
                                   '.s')
        open(file_name, 'wt').write(self.program)

    def generate_program(self, iterations, nInstructions):
        self.__add_header(iterations)
        self.init_registers()
        # self.__force_alignment()
        self.__add_loop_label()
        for i in range(0, nInstructions):
            self.program += self._add_random_instruction()
        self.__add_footer()
        self.__save_program(iterations, nInstructions)

    def set_dir(self, newDir):
        self.dir = newDir

    def set_prefix(self, newPrefix):
        self.prefix = newPrefix
