# xtc matmul on Z80: i8 / i16 / i32 variants of ../test_xtc_i32.py's kernel,
# compiled with SDCC and run on the cycle-accurate z80 simulator.
#
# Everything dtype-specific is generated from the template below; the
# shared sources live in common/ (see README.md).

CC ?= gcc
PYTHON ?= $(PROJECT_ROOT)/venv/bin/python
PROJECT_ROOT := ..
SDCC_BIN := $(PROJECT_ROOT)/tools/sdcc-4.6.0/bin
SDCC := $(SDCC_BIN)/sdcc
ASZ80 := $(SDCC_BIN)/sdasz80
SDOBJCOPY := $(SDCC_BIN)/sdobjcopy
# The xtc-generated multiplies lower to SDCC z80 runtime helpers
# (__mulint / __mullong); SDCC's z80 library provides them.
SDCC_Z80_LIB := $(PROJECT_ROOT)/tools/sdcc-4.6.0/share/sdcc/lib/z80/z80.lib

Z80_CORE := $(PROJECT_ROOT)/z80
BUILD := build
GEN := gen
COMMON := common
SIM := $(BUILD)/z80sim

# K shrunk from 512 (test_xtc_i32.py) to 128 so the operands fit the Z80's
# 64K flat address space; see gen_matmul.py.
SDCCFLAGS := -mz80 --std-c11 --nostdinc --nostdlib --no-std-crt0 \
             --code-loc 0x0000 --data-loc 0x8000 -I$(COMMON)

DTYPES := i8 i16 i32
ELT.i8  := int8_t
ELT.i16 := int16_t
ELT.i32 := int32_t

all: $(SIM) $(DTYPES:%=$(BUILD)/%/matmul.bin)

$(BUILD):
	mkdir -p $@

# --- host-side cycle-accurate simulator (shared) -----------------------------
$(SIM): $(COMMON)/sim/main.c $(Z80_CORE)/z80.c $(Z80_CORE)/z80.h | $(BUILD)
	$(CC) -O2 -std=c99 -Wall -Wextra -I$(Z80_CORE) -o $@ $(COMMON)/sim/main.c $(Z80_CORE)/z80.c

# --- crt0 (shared by all variants) ------------------------------------------
$(BUILD)/crt0.rel: $(COMMON)/crt0.s | $(BUILD)
	cp $(COMMON)/crt0.s $(BUILD)/crt0.s
	$(ASZ80) -xlos -g -o $@ $(BUILD)/crt0.s && rm -f $(BUILD)/crt0.s

# --- per-dtype rules (evaluated from the template below in make) -------------
# $(1): dtype shorthand (i8/i16/i32)   $(2): element typedef (intN_t)
define dtype_rules
$$(GEN)/$(1)/matmul_$(1)_mlir.c: gen_matmul.py
	$$(PYTHON) gen_matmul.py $(1)

$$(BUILD)/$(1):
	mkdir -p $$@

$$(BUILD)/$(1)/main.rel: $$(COMMON)/main.c $$(COMMON)/xtc_crt/xtc_crt.h | $$(BUILD)/$(1)
	$$(SDCC) $$(SDCCFLAGS) -DMATMUL_ELT=$(2) -c -o $$@ $$(COMMON)/main.c

$$(BUILD)/$(1)/matmul_$(1)_mlir.rel: $$(GEN)/$(1)/matmul_$(1)_mlir.c $$(COMMON)/xtc_crt/xtc_crt.h | $$(BUILD)/$(1)
	$$(SDCC) $$(SDCCFLAGS) -DMATMUL_ELT=$(2) -c -o $$@ $$<

$$(BUILD)/$(1)/matmul.ihx: $$(BUILD)/crt0.rel $$(BUILD)/$(1)/main.rel $$(BUILD)/$(1)/matmul_$(1)_mlir.rel
	$$(SDCC) $$(SDCCFLAGS) -o $$@ $$^ $$(SDCC_Z80_LIB)

$$(BUILD)/$(1)/matmul.bin: $$(BUILD)/$(1)/matmul.ihx
	$$(SDOBJCOPY) -I ihex -O binary $$< $$@

gen-$(1): $$(GEN)/$(1)/matmul_$(1)_mlir.c

run-$(1): $$(SIM) $$(BUILD)/$(1)/matmul.bin
	$$(SIM) $$(BUILD)/$(1)/matmul.bin 0x0000

test-$(1): $$(SIM) $$(BUILD)/$(1)/matmul.bin
	@$$(SIM) $$(BUILD)/$(1)/matmul.bin 0x0000 > $$(BUILD)/$(1)/run.log || true
	@cat $$(BUILD)/$(1)/run.log
	@grep -q '^PASS' $$(BUILD)/$(1)/run.log && echo "[test $(1)] PASS" || { echo "[test $(1)] FAILED"; exit 1; }
endef

$(foreach d,$(DTYPES),$(eval $(call dtype_rules,$(d),$(ELT.$(d)))))

# --- aggregates ---------------------------------------------------------------
gen: $(DTYPES:%=gen-%)
run: $(DTYPES:%=run-%)

test: $(SIM) $(DTYPES:%=$(BUILD)/%/matmul.bin)
	@rc=0; for d in $(DTYPES); do \
	   echo "=== $$d"; \
	   $(SIM) $(BUILD)/$$d/matmul.bin 0x0000 2>&1 > $(BUILD)/$$d/run.log || true; \
	   cat $(BUILD)/$$d/run.log; \
	   if grep -q '^PASS' $(BUILD)/$$d/run.log; then echo "[test $$d] PASS"; \
	   else echo "[test $$d] FAILED"; rc=1; fi; \
	 done; exit $$rc

clean:
	rm -rf $(BUILD) $(GEN)

.PHONY: all gen run test clean $(DTYPES:%=gen-%) $(DTYPES:%=run-%) $(DTYPES:%=test-%)
