CC=riscv64-unknown-elf-gcc
CFLAGS=-DPREALLOCATE=1 -march=rv64g -mcmodel=medany -static -std=gnu99 -O0 -ffast-math -fno-common -fno-builtin-printf
LDFLAGS=-static -nostdlib -nostartfiles -lm -lgcc
VERILATOR=/home/override/rocket-chip/emulator/emulator-freechips.rocketchip.system-freechips.rocketchip.system.DefaultConfig

SRC_DIR=test-programs
OBJ_DIR=bin
COMMON=ext

GEN:=$(shell python gen-templates.py -i 10 -n 50)
SRCS=$(wildcard $(SRC_DIR)/*.s)
OBJS=$(patsubst $(SRC_DIR)/%.s,$(OBJ_DIR)/%.riscv.hex,$(SRCS))



all: $(OBJS)

$(OBJ_DIR)/%.riscv.hex: $(OBJ_DIR)/%.riscv
	elf2hex 16 512 $^ > ${@}

$(OBJ_DIR)/%.riscv : $(SRC_DIR)/%.s
	$(CC) $(CFLAGS) -I $(COMMON)/ -o $@ $^ $(LDFLAGS) -T $(COMMON)/boot.ld

# $(OBJ_DIR)/%.riscv : $(SRC_DIR)/%.s
# 	$(CC) $(CFLAGS) -I $(COMMON)/ -o $@ $^ $(LDFLAGS) -T $(COMMON)/boot.ld

run: $(OBJS)
	$(VERILATOR) +max-cycles=10000000 +loadmem=$^

clean:
	rm $(OBJ_DIR)/*  $(SRC_DIR)/*


# # riscv64-unknown-elf-objdump --disassemble-all --disassemble-zeroes --section=.text --section=.text.startup --section=.data ${1}.riscv > ${1}.riscv.dump
#
# # elf2hex 16 512 ${1}.riscv > ${1}.riscv.hex
