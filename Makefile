# Makefile for Projection Method
# Updated for new directory structure

CXX = g++
CC = cc
BASE_CXXFLAGS = -std=c++17 -Wall -Wextra
BASE_CFLAGS = -std=c11 -Wall -Wextra
OPT_FLAGS = -O3
CXXFLAGS = $(BASE_CXXFLAGS) $(OPT_FLAGS)
CFLAGS = $(BASE_CFLAGS) $(OPT_FLAGS)
LDFLAGS =

# Detect OS
UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Darwin)
    # macOS
    CXX = clang++
    CC = clang
    LIBOMP_PREFIX ?= $(shell brew --prefix libomp 2>/dev/null)
    ifeq ($(LIBOMP_PREFIX),)
        LIBOMP_PREFIX = /opt/homebrew/opt/libomp
    endif
endif

USE_OPENMP ?= 0
USE_SIMD ?= 0

# Directories
SRC_DIR = cpp_src
C_SRC_DIR = c_src
BUILD_DIR = build
SCRIPT_DIR = scripts

PROFILE_MODE ?= release
PROFILE_MODE_FLAGS =
ifeq ($(PROFILE_MODE),perf)
    PROFILE_MODE_FLAGS = -g -O3 -fno-omit-frame-pointer
else ifeq ($(PROFILE_MODE),gprof)
    PROFILE_MODE_FLAGS = -pg -g -O2
    LDFLAGS += -pg
else ifeq ($(PROFILE_MODE),callgrind)
    PROFILE_MODE_FLAGS = -g -O2
endif

CXXFLAGS = $(BASE_CXXFLAGS) $(OPT_FLAGS) $(PROFILE_MODE_FLAGS)
CFLAGS = $(BASE_CFLAGS) $(OPT_FLAGS) $(PROFILE_MODE_FLAGS)

ifeq ($(USE_OPENMP),1)
    ifeq ($(UNAME_S),Darwin)
        OPENMP_CFLAGS = -Xpreprocessor -fopenmp -I$(LIBOMP_PREFIX)/include
        OPENMP_LDFLAGS = -L$(LIBOMP_PREFIX)/lib -lomp
    else
        OPENMP_CFLAGS = -fopenmp
        OPENMP_LDFLAGS = -fopenmp
    endif
    CXXFLAGS += $(OPENMP_CFLAGS)
    CFLAGS += $(OPENMP_CFLAGS)
    LDFLAGS += $(OPENMP_LDFLAGS)
endif

ifeq ($(USE_SIMD),1)
    SIMD_CFLAGS = -DPROJECTION_C_USE_SIMD
    ifeq ($(UNAME_S),Darwin)
        ifeq ($(shell uname -m),arm64)
            $(warning USE_SIMD=1 requested on Apple Silicon; AVX2/FMA flags are skipped and scalar fallback will be used)
        else
            SIMD_CFLAGS += -mavx2 -mfma
        endif
    else
        SIMD_CFLAGS += -mavx2 -mfma
    endif
    CFLAGS += $(SIMD_CFLAGS)
endif

# Python environment
CONDA_ENV = SWPUCompetiton
PYTHON = /opt/homebrew/Caskroom/miniconda/base/bin/conda run -n $(CONDA_ENV) python

# Target and sources
TARGET = projection_method
SOURCES = $(SRC_DIR)/main.cpp $(SRC_DIR)/projection_method.cpp $(SRC_DIR)/file_io_improved.cpp
C_SOURCES = $(C_SRC_DIR)/projection_c.c
HEADERS = $(SRC_DIR)/projection_method.h $(SRC_DIR)/cnpy_simple.h $(C_SRC_DIR)/projection_c.h
OBJECTS = $(BUILD_DIR)/main.o $(BUILD_DIR)/projection_method.o $(BUILD_DIR)/file_io_improved.o $(BUILD_DIR)/projection_c.o

.PHONY: all clean run test profile-perf profile-gprof profile-callgrind profile-openmp help

all: $(TARGET)

$(TARGET): $(OBJECTS)
	$(CXX) $(OBJECTS) -o $(TARGET) $(LDFLAGS)
	@echo "Build complete: $(TARGET)"

$(BUILD_DIR)/%.o: $(SRC_DIR)/%.cpp $(HEADERS) | $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) -I$(SRC_DIR) -I$(C_SRC_DIR) -c $< -o $@

$(BUILD_DIR)/projection_c.o: $(C_SRC_DIR)/projection_c.c $(C_SRC_DIR)/projection_c.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) -I$(C_SRC_DIR) -c $< -o $@

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

clean:
	rm -rf $(BUILD_DIR)
	rm -f $(TARGET)
	rm -f *.txt
	@echo "Clean complete"

run: $(TARGET)
	./$(TARGET)

test: $(TARGET)
	@echo "Running calculation..."
	./$(TARGET) 1.0 0.025 3395 3400 0.5
	@echo ""
	@echo "Running validation..."
	$(PYTHON) $(SCRIPT_DIR)/check_output.py

profile-perf:
	$(MAKE) clean
	$(MAKE) PROFILE_MODE=perf

profile-gprof:
	$(MAKE) clean
	$(MAKE) PROFILE_MODE=gprof

profile-callgrind:
	$(MAKE) clean
	$(MAKE) PROFILE_MODE=callgrind

profile-openmp:
	$(MAKE) clean
	$(MAKE) USE_OPENMP=1 PROFILE_MODE=perf

help:
	@echo "Available targets:"
	@echo "  all         - Build the project (default)"
	@echo "  clean       - Remove build artifacts"
	@echo "  run         - Build and run with default parameters"
	@echo "  test        - Build, run, and validate output"
	@echo "  profile-perf      - Clean build with perf-friendly flags (-g -O3 -fno-omit-frame-pointer)"
	@echo "  profile-gprof     - Clean build with gprof flags (-pg -g -O2)"
	@echo "  profile-callgrind - Clean build with callgrind-friendly flags (-g -O2)"
	@echo "  profile-openmp    - Clean OpenMP perf build (USE_OPENMP=1)"
	@echo ""
	@echo "Optional variables:"
	@echo "  USE_OPENMP=1      - Enable OpenMP parallelism"
	@echo "  USE_SIMD=1        - Enable optional AVX2/FMA SIMD path for projection_c.c"
	@echo ""
	@echo "Examples:"
	@echo "  make test"
	@echo "  make profile-perf"
	@echo "  make profile-openmp"
	@echo "  make USE_SIMD=1"
	@echo "  make USE_OPENMP=1 USE_SIMD=1"
