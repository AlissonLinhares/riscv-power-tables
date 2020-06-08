#!/usr/bin/python

from src.default_template import *
from src.basic_templates import *
from src.jump_templates import *
from src.load_store_templates import *

import argparse
import random

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
