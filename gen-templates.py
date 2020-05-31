#!/usr/bin/python

import argparse
import random
import string
import os
import numpy
import struct


class InstGenerator:
    _templateHeader = """
        .text
        .align  2
        .globl _start
_start:
        .globl  main
        .type   main, @function
main:
        li    t0, $iterations

"""

    _templateFooter = """

        addi    t0, t0, -1
        bne     t0, x0, loop
        j       0x1FF0
end:    beq     x0, x0, end

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

    _FLOAT_VALUES = [
        0.0, # zero
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

    def __init__(self, instruction, use_floating_values = False):
        self.instruction = instruction
        self.program = ''
        self.dir = 'test-programs'
        self.prefix = ''
        self.use_floating_values = use_floating_values

        if self.use_floating_values:
            self.srcReg = [
                'f0',  'f1',  'f2',  'f3',  'f4',  'f5',  'f6',  'f7',  'f8',
                'f9', 'f10', 'f11', 'f12', 'f13', 'f14', 'f15', 'f16', 'f17',
               'f18', 'f19', 'f20', 'f21', 'f22', 'f23', 'f24', 'f25', 'f26',
               'f27', 'f28', 'f29', 'f30', 'f31'
            ]
        else:
            self.srcReg = [
                 'x0',  'x1',  'x2',  'x3',  'x4',  'x5',  'x6',  'x7',  'x8',
                 'x9', 'x10', 'x11', 'x12', 'x13', 'x14', 'x15', 'x16', 'x17',
                'x18', 'x19', 'x20', 'x21', 'x22', 'x23', 'x24', 'x25', 'x26',
                'x27', 'x28', 'x29', 'x30', 'x31'
            ]

        self.dstReg = []

    def init_registers(self, registers):
        if self.use_floating_values:
            for r in registers:
                label = "." + r +"_DATA"
                self.program += "        lui a5,%hi(" + label + ")\n"
                self.program += "        flw " + r + ",%lo(" + label + ")(a5)\n"
                self.alloc_single_value(random.choice(self._FLOAT_VALUES), label)
        else:
            for r in registers:
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
        self._templateFooter += "%s:\n\
        .word  %d\n\
        .word  %d\n\
        .align  3" % (label, int(bstr[32:64],2), int(bstr[0:32],2))

    def ReserveDestinationRegisters(self, number):
        for i in range(0, number):
            register = random.choice(self.srcReg)
            self.srcReg.remove(register)
            self.dstReg.append(register)

    def _add_random_instruction(self):
        return '# No template given\n'

    def __add_header(self, iterations):
        self.program += string.replace(self._templateHeader, '$iterations', str(iterations))

    def __add_loop_label(self):
        self.program += "\nloop:\n"

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
        self.init_registers(self.srcReg)
        self.init_registers(self.dstReg)
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
        return "        %s    %s, %d\n" % (self.instruction,
                                           random.choice(self.srcReg),
                                           random.randint(0, 2 ** 20 - 1))

# opcode rs2 rs1 opcode rd opcode
class TypeR(InstGenerator):
    def _add_random_instruction(self):
        return "        %s    %s, %s, %s\n" % (self.instruction,
                                               random.choice(self.dstReg),
                                               random.choice(self.srcReg),
                                               random.choice(self.srcReg))

# opcode rs2 rs1 opcode rd opcode
class TypeRD(TypeR):
    def init_registers(self, registers):
        for r in registers:
            value = 2 ** numpy.random.choice(self._WRANGE, p=self._RAND_WEIGHT)
            self.program += "        li %s, %d\n" % (r, value)

# opcode shamt rs1 opcode rd opcode
class TypeRS(InstGenerator):
    def _add_random_instruction(self):
        return "        %s    %s, %s, %d\n" % (self.instruction,
                                               random.choice(self.dstReg),
                                               random.choice(self.srcReg),
                                               random.randint(0, 31))


# imm[11:0] rs1 opcode rd opcode
class TypeI(InstGenerator):
    def _add_random_instruction(self):
        return "        %s    %s, %s, %d\n" % (self.instruction,
                                               random.choice(self.dstReg),
                                               random.choice(self.srcReg),
                                               random.randint(0, 2047))

# imm[11:0] rs1 opcode rd opcode
class TypeILS(InstGenerator):
    def __init__(self, instruction, baseAddress, endAddress):
        InstGenerator.__init__(self, instruction)
        self.baseAddress = baseAddress
        self.endAddress = endAddress
        self.range = int((endAddress - baseAddress) / 4)

    def _add_random_instruction(self):
        return "        %s    %s, %d(%s)\n" % (self.instruction,
                                               random.choice(self.dstReg),
                                               self.baseAddress + 4 * random.randint(0, self.range),
                                               random.choice(self.srcReg))

class TypeR4(InstGenerator):
    def _add_random_instruction(self):
        return "        %s    %s, %s, %s, %s\n" % (self.instruction,
                                           random.choice(self.dstReg),
                                           random.choice(self.srcReg),
                                           random.choice(self.srcReg),
                                           random.choice(self.srcReg))

class TypeR2(InstGenerator):
    def _add_random_instruction(self):
        return "        %s    %s, %s\n" % (self.instruction,
                                           random.choice(self.dstReg),
                                           random.choice(self.srcReg))


if __name__ == '__main__':
    random.seed()

    parser = argparse.ArgumentParser(description = 'Generate characterization programs for Instruction Based Power Models')

    parser.add_argument('-i', '--iterations', type=int, required=True, help='Number of loop iterations')
    parser.add_argument('-n', '--number', type=int, required=True, help='Number of instructions to include in the loop body')
    parser.add_argument('-o', '--output', required=False, help='Output directory for template programs')
    parser.add_argument('-v', '--verbose', required=False, action='store_true', help='Show debug information')
    parser.add_argument('-p', '--prefix', required=False, help='Add this prefix to all filenames')
    args = parser.parse_args()

    branchInstructions = ['beq', 'bne', 'blt', 'bge', 'bltu', 'bgeu']
    jumpInstructions = ['jal', 'jalr']


    templates = [
        # RV32I
        TypeU("lui"),
        TypeU("auipc"),

        TypeILS("lb", 0, 512),
        TypeILS("lh", 0, 512),
        TypeILS("lw", 0, 512),
        TypeILS("lbu", 0, 512),
        TypeILS("lhu", 0, 512),
        TypeILS("sb", 0, 512),
        TypeILS("sh", 0, 512),
        TypeILS("sw", 0, 512),

        TypeI("addi"),
        TypeI("slti"),
        TypeI("sltiu"),
        TypeI("xori"),
        TypeI("ori"),
        TypeI("andi"),

        TypeRS("slli"),
        TypeRS("srli"),
        TypeRS("srai"),
        TypeR("add"),
        TypeR("sub"),
        TypeR("sll"),
        TypeR("slt"),
        TypeR("sltu"),
        TypeR("xor"),
        TypeR("srl"),
        TypeR("sra"),
        TypeR("or"),
        TypeR("and"),

        # RV64I
        TypeILS("lwu", 0, 512),
        TypeILS("ld", 0, 512),
        TypeILS("sd", 0, 512),
        TypeI("addiw"),
        TypeRS("slliw"),
        TypeRS("srliw"),
        TypeRS("sraiw"),

        TypeR("addw"),
        TypeR("subw"),
        TypeR("sllw"),
        TypeR("srlw"),
        TypeR("sraw"),

        # RV32M
        TypeR("mul"),
        TypeR("mulh"),
        TypeR("mulhsu"),
        TypeR("mulhu"),
        TypeRD("div"),
        TypeRD("divu"),
        TypeRD("rem"),
        TypeRD("remu"),

        # RV64M
        TypeR("mulw"),
        TypeRD("divw"),
        TypeRD("divuw"),
        TypeRD("remw"),
        TypeRD("remuw"),

        # RV32F
        TypeR4("fmadd.s", True),
        TypeR4("fmsub.s", True),
        TypeR4("fnmsub.s", True),
        TypeR4("fnmadd.s", True),
        TypeR("fadd.s", True),
        TypeR("fsub.s", True),
        TypeR("fmul.s", True),
        TypeR("fdiv.s", True), # TODO: Remove zero
        TypeR2("fsqrt.s", True),
        TypeR("fsgnj.s", True),
        TypeR("fsgnjn.s", True),
        TypeR("fsgnjx.s", True),
        TypeR("fmin.s", True),
        TypeR("fmax.s", True),

        # RV32D
        TypeR4("fmadd.d", True),
        TypeR4("fmsub.d", True),
        TypeR4("fnmsub.d", True),
        TypeR4("fnmadd.d", True),
        TypeR("fadd.d", True),
        TypeR("fsub.d", True),
        TypeR("fmul.d", True),
        TypeR("fdiv.d", True), # TODO: Remove zero
        TypeR2("fsqrt.d", True),
        TypeR("fsgnj.d", True),
        TypeR("fsgnjn.d", True),
        TypeR("fsgnjx.d", True),
        TypeR("fmin.d", True),
        TypeR("fmax.d", True)
    ]


    for template in templates:
        template.ReserveDestinationRegisters(6)

        if (args.verbose):
            print ('Instruction:' + template.instruction)
        if (args.output is not None):
            template.set_dir(args.output)
        if (args.prefix is not None):
            template.set_prefix(args.prefix)

        template.generate_program(args.iterations, args.number)
