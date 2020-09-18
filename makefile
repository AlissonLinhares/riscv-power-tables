CC=$(RISCV)/riscv64-unknown-elf-gcc
HEX=$(RISCV)/elf2hex
CFLAGS=-DPREALLOCATE=1 -march=rv64imfd -mcmodel=medany -static -std=gnu99 -O0
LDFLAGS=-static -nostdlib -nostartfiles -lm -lgcc
SPIKE=$(RISCV)/spike

SRC_DIR=test-programs
OBJ_DIR=bin
LOG_DIR=log
COMMON=ext

GEN:=$(shell python gen-test-programs.py -i 10 -n 20 -p "0_")
GEN:=$(shell python gen-test-programs.py -i 10 -n 20 -p "1_")
GEN:=$(shell python gen-test-programs.py -i 10 -n 20 -p "2_")
GEN:=$(shell python gen-test-programs.py -i 10 -n 20 -p "3_")
GEN:=$(shell python gen-test-programs.py -i 10 -n 20 -p "4_")
GEN:=$(shell python gen-test-programs.py -i 10 -n 20 -p "5_")
GEN:=$(shell python gen-test-programs.py -i 10 -n 20 -p "6_")
GEN:=$(shell python gen-test-programs.py -i 10 -n 20 -p "7_")
GEN:=$(shell python gen-test-programs.py -i 10 -n 20 -p "8_")
GEN:=$(shell python gen-test-programs.py -i 10 -n 20 -p "9_")

SRCS=$(wildcard $(SRC_DIR)/*.s)
OBJS=$(patsubst $(SRC_DIR)/%.s,$(OBJ_DIR)/%.riscv.hex,$(SRCS))
TESTS=$(patsubst $(SRC_DIR)/%.s,$(OBJ_DIR)/%.riscv,$(SRCS))

EXPECTED_RESULT="User fetch segfault @ 0x0000000000001ff0"

.PRECIOUS: $(OBJ_DIR)/%.riscv

all: $(OBJ_DIR) $(LOG_DIR) $(OBJS)

$(OBJ_DIR)/%.riscv.hex: $(OBJ_DIR)/%.riscv
	$(HEX) 8 4096 $^ > ${@}

$(OBJ_DIR)/%.riscv : $(SRC_DIR)/%.s
	$(CC) $(CFLAGS) -I $(COMMON)/ -o $@ $^ $(LDFLAGS) -T $(COMMON)/boot.ld

$(LOG_DIR):
	mkdir $(LOG_DIR)

$(OBJ_DIR):
	mkdir $(OBJ_DIR)

test: $(OBJS)
	@{  echo "************************* Tests ******************************"; \
		test_failed=0; \
		test_passed=0; \
		for test in $(TESTS); do \
			printf "Running $$test: "; \
			output=$(LOG_DIR)/`basename $$test`.log; \
			$(SPIKE) pk $$test > $$output; \
			errors=`cat $$output | grep $(EXPECTED_RESULT) | wc -l`; \
			if [ "$$errors" -eq 1 ]; then \
				printf "\033[0;32mPASSED\033[0m\n"; \
				test_passed=$$((test_passed+1)); \
			else \
				printf "\033[0;31mFAILED\033[0m\n"; \
				test_failed=$$((test_failed+1)); \
			fi; \
		done; \
		echo "*********************** Summary ******************************"; \
		echo "- $$test_passed tests passed"; \
		echo "- $$test_failed tests failed"; \
		echo "**************************************************************"; \
	}

clean:
	rm $(OBJ_DIR)/*  $(SRC_DIR)/* $(LOG_DIR)/*
