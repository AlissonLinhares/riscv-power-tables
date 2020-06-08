#!/usr/bin/python

import argparse
import random
import string
import os
import numpy
import struct
import statistics

from string import Template
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

# opcode rs2 rs1 opcode rd opcode
class TypeRD(TypeR):
    def init_registers(self):
        # div 0, 0 is not allowed
        self.srcReg.pop(0)

        for r in self.srcReg:
            value = 2 ** numpy.random.choice(self._WRANGE, p=self._RAND_WEIGHT)
            self.program += "        li %s, %d\n" % (r, value)

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

# imm[11:0] rs1 opcode rd opcode
class TypeILS(InstGenerator):
    def __init__(self, instruction, format, baseAddress, endAddress):
        InstGenerator.__init__(self, instruction, format)
        self.baseAddress = baseAddress
        self.endAddress = endAddress

    def init_registers(self):
        for r in self.srcReg[1:]:
            self.program += "        li %s, %d\n" % (r, random.randint(self.baseAddress + 2048, self.endAddress - 2048))

    def _add_random_instruction(self):
        return "        %s %s, %d(%s)\n" % (self.instruction,
                                            random.choice(self.dstReg),
                                            random.randint(0, 2047),
                                            random.choice(self.srcReg[1:]))

class TypeILSF(TypeILS):
    def init_registers(self):
        super(TypeILS, self).init_registers()

        for r in self._ALL_VALID_INT_TGTS:
            self.program += "        li %s, %d\n" % (r, random.randint(self.baseAddress + 2048, self.endAddress - 2048))

    def _add_random_instruction(self):
        return "        %s %s, %d(%s)\n" % (self.instruction,
                                            random.choice(self._ALL_VALID_FLOAT_TGTS),
                                            random.randint(0, 2047),
                                            random.choice(self._ALL_VALID_INT_TGTS))

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



if __name__ == '__main__':
    random.seed()

    parser = argparse.ArgumentParser(description = 'Generate characterization programs for Instruction Based Power Models')

    parser.add_argument('-i', '--iterations', type=int, required=True, help='Number of loop iterations')
    parser.add_argument('-n', '--number', type=int, required=True, help='Number of instructions to include in the loop body')
    parser.add_argument('-o', '--output', required=False, help='Output directory for template programs')
    parser.add_argument('-v', '--verbose', required=False, action='store_true', help='Show debug information')
    parser.add_argument('-p', '--prefix', required=False, help='Add this prefix to all filenames')
    args = parser.parse_args()









    templates = [
        InstGenerator("baseline"),

        # RV32I
        TypeU("lui", Extension.I),
        TypeU("auipc", Extension.I),
        TypeJ("jal", Extension.I),
        TypeJR("jalr", Extension.I),

        TypeB("beq", Extension.I, TypeB.EQUAL_TST),
        TypeB("bne", Extension.I, TypeB.LOWER_TST),
        TypeB("blt", Extension.I, TypeB.LOWER_TST),
        TypeB("bge", Extension.I, TypeB.GRATER_TST),
        TypeB("bltu", Extension.I, TypeB.LOWER_TST),
        TypeB("bgeu", Extension.I, TypeB.GRATER_TST),

        TypeB("beq", Extension.I, TypeB.LOWER_TST, "not_taken_"),
        TypeB("bne", Extension.I, TypeB.EQUAL_TST, "not_taken_"),
        TypeB("blt", Extension.I, TypeB.GRATER_TST, "not_taken_"),
        TypeB("bge", Extension.I, TypeB.LOWER_TST, "not_taken_"),
        TypeB("bltu", Extension.I, TypeB.GRATER_TST, "not_taken_"),
        TypeB("bgeu", Extension.I, TypeB.LOWER_TST, "not_taken_"),

        TypeILS("lb", Extension.I, 0x10000000, 0x10080000),
        TypeILS("lh", Extension.I, 0x10000000, 0x10080000),
        TypeILS("lw", Extension.I, 0x10000000, 0x10080000),
        TypeILS("lbu", Extension.I, 0x10000000, 0x10080000),
        TypeILS("lhu", Extension.I, 0x10000000, 0x10080000),
        TypeILS("sb", Extension.I, 0x10000000, 0x10080000),
        TypeILS("sh", Extension.I, 0x10000000, 0x10080000),
        TypeILS("sw", Extension.I, 0x10000000, 0x10080000),
        TypeI("addi", Extension.I),
        TypeI("slti", Extension.I),
        TypeI("sltiu", Extension.I),
        TypeI("xori", Extension.I),
        TypeI("ori", Extension.I),
        TypeI("andi", Extension.I),
        TypeRS("slli", Extension.I),
        TypeRS("srli", Extension.I),
        TypeRS("srai", Extension.I),
        TypeR("add", Extension.I),
        TypeR("sub", Extension.I),
        TypeR("sll", Extension.I),
        TypeR("slt", Extension.I),
        TypeR("sltu", Extension.I),
        TypeR("xor", Extension.I),
        TypeR("srl", Extension.I),
        TypeR("sra", Extension.I),
        TypeR("or", Extension.I),
        TypeR("and", Extension.I),

        # RV64I
        TypeILS("lwu", Extension.I, 0x10000000, 0x10080000),
        TypeILS("ld", Extension.I, 0x10000000, 0x10080000),
        TypeILS("sd", Extension.I, 0x10000000, 0x10080000),
        TypeI("addiw", Extension.I),
        TypeRS("slliw", Extension.I),
        TypeRS("srliw", Extension.I),
        TypeRS("sraiw", Extension.I),
        TypeR("addw", Extension.I),
        TypeR("subw", Extension.I),
        TypeR("sllw", Extension.I),
        TypeR("srlw", Extension.I),
        TypeR("sraw", Extension.I),

        # RV32M
        TypeR("mul", Extension.I),
        TypeR("mulh", Extension.I),
        TypeR("mulhsu", Extension.I),
        TypeR("mulhu", Extension.I),
        TypeRD("div", Extension.I),
        TypeRD("divu", Extension.I),
        TypeRD("rem", Extension.I),
        TypeRD("remu", Extension.I),

        # RV64M
        TypeR("mulw", Extension.I),
        TypeRD("divw", Extension.I),
        TypeRD("divuw", Extension.I),
        TypeRD("remw", Extension.I),
        TypeRD("remuw", Extension.I),

        # RV32F
        TypeILSF("flw", Extension.S, 0x10000000, 0x10080000),
        TypeILSF("fsw", Extension.S, 0x10000000, 0x10080000),
        TypeR4("fmadd.s", Extension.S),
        TypeR4("fmsub.s", Extension.S),
        TypeR4("fnmsub.s", Extension.S),
        TypeR4("fnmadd.s", Extension.S),
        TypeR("fadd.s", Extension.S),
        TypeR("fsub.s", Extension.S),
        TypeR("fmul.s", Extension.S),
        TypeR("fdiv.s", Extension.S),
        TypeR2("fsqrt.s", Extension.S),
        TypeR("fsgnj.s", Extension.S),
        TypeR("fsgnjn.s", Extension.S),
        TypeR("fsgnjx.s", Extension.S),
        TypeR("fmin.s", Extension.S),
        TypeR("fmax.s", Extension.S),
        TypeR2DI("fcvt.w.s", Extension.S),
        TypeR2DI("fcvt.wu.s", Extension.S),
        TypeR2DI("fmv.x.w", Extension.S),
        TypeRF("feq.s", Extension.S),
        TypeRF("flt.s", Extension.S),
        TypeRF("fle.s", Extension.S),
        TypeR2DI("fclass.s", Extension.S),
        TypeR2DF("fcvt.s.w", Extension.I),
        TypeR2DF("fcvt.s.wu", Extension.I),
        TypeR2DF("fmv.w.x", Extension.I), # TODO: inicializar x com um numero real

        # RV32D
        TypeILSF("fld", Extension.D, 0x10000000, 0x10080000),
        TypeILSF("fsd", Extension.D, 0x10000000, 0x10080000),
        TypeR4("fmadd.d", Extension.D),
        TypeR4("fmsub.d", Extension.D),
        TypeR4("fnmsub.d", Extension.D),
        TypeR4("fnmadd.d", Extension.D),
        TypeR("fadd.d", Extension.D),
        TypeR("fsub.d", Extension.D),
        TypeR("fmul.d", Extension.D),
        TypeR("fdiv.d", Extension.D),
        TypeR2("fsqrt.d", Extension.D),
        TypeR("fsgnj.d" , Extension.D),
        TypeR("fsgnjn.d", Extension.D),
        TypeR("fsgnjx.d", Extension.D),
        TypeR("fmin.d", Extension.D),
        TypeR("fmax.d", Extension.D),
        TypeR2("fcvt.s.d", Extension.D),
        TypeR2("fcvt.d.s", Extension.S),
        TypeRF("feq.d", Extension.D),
        TypeRF("flt.d", Extension.D),
        TypeRF("fle.d", Extension.D),
        TypeR2DI("fclass.d", Extension.D),
        TypeR2DI("fcvt.w.d", Extension.D),
        TypeR2DI("fcvt.wu.d", Extension.D),
        TypeR2DF("fcvt.d.w", Extension.I),
        TypeR2DF("fcvt.d.wu", Extension.I),

        # RV64F
        TypeR2DI("fcvt.l.s", Extension.S),
        TypeR2DI("fcvt.lu.s", Extension.S),
        TypeR2DF("fcvt.s.l", Extension.I),
        TypeR2DF("fcvt.s.lu", Extension.I),

        # RV64D
        TypeR2DI("fcvt.l.d", Extension.D),
        TypeR2DI("fcvt.lu.d", Extension.D),
        TypeR2DI("fmv.x.d", Extension.D),
        TypeR2DF("fcvt.d.l", Extension.I),
        TypeR2DF("fcvt.d.lu", Extension.I),
        TypeR2DF("fmv.d.x", Extension.I) # TODO: iniciar x com um valor real
    ]

    for template in templates:
        template.reserve_destination_registers(6)

        if (args.verbose):
            print ('Instruction:' + template.instruction)
        if (args.output is not None):
            template.set_dir(args.output)
        if (args.prefix is not None):
            template.set_prefix(args.prefix)

        template.generate_program(args.iterations, args.number)
