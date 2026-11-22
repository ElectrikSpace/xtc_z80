CC ?= gcc
PROJECT_ROOT := ..
SDCC_BIN := $(PROJECT_ROOT)/tools/sdcc-4.6.0/bin
SDCC := $(SDCC_BIN)/sdcc
ASZ80 := $(SDCC_BIN)/sdasz80
SDOBJOCOPY := $(SDCC_BIN)/sdobjcopy

Z80_CORE := $(PROJECT_ROOT)/z80
BUILD := build
SIM := $(BUILD)/z80sim

SDCCFLAGS := -mz80 --std-c11 --nostdinc --nostdlib --no-std-crt0 \
             --code-loc 0x0000 --data-loc 0x8000

all: $(SIM) $(BUILD)/hello.bin

$(BUILD):
	mkdir -p $(BUILD)

$(SIM): sim/main.c $(Z80_CORE)/z80.c $(Z80_CORE)/z80.h | $(BUILD)
	$(CC) -O2 -std=c99 -Wall -Wextra -I$(Z80_CORE) -o $@ sim/main.c $(Z80_CORE)/z80.c

$(BUILD)/crt0.rel: src/crt0.s | $(BUILD)
	cp src/crt0.s $(BUILD)/crt0.s
	$(ASZ80) -xlos -g -o $(BUILD)/crt0.rel $(BUILD)/crt0.s && rm -f $(BUILD)/crt0.s

$(BUILD)/hello.rel: src/hello.c | $(BUILD)
	$(SDCC) $(SDCCFLAGS) -c -o $@ $<

$(BUILD)/hello.ihx: $(BUILD)/crt0.rel $(BUILD)/hello.rel
	$(SDCC) $(SDCCFLAGS) -o $@ $^

$(BUILD)/hello.bin: $(BUILD)/hello.ihx
	$(SDOBJOCOPY) -I ihex -O binary $< $@

run: all
	$(SIM) $(BUILD)/hello.bin 0x0000

clean:
	rm -rf $(BUILD)

.PHONY: all run clean
