# Makefile for Projection Method
# Updated for new directory structure

CXX = g++
CC = cc
CXXFLAGS = -std=c++17 -Wall -Wextra -O3
CFLAGS = -std=c11 -Wall -Wextra -O3
LDFLAGS =

# Detect OS
UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Darwin)
    # macOS
    CXX = clang++
endif

# Directories
SRC_DIR = cpp_src
C_SRC_DIR = c_src
BUILD_DIR = build
SCRIPT_DIR = scripts

# Python environment
CONDA_ENV = SWPUCompetiton
PYTHON = /opt/homebrew/Caskroom/miniconda/base/bin/conda run -n $(CONDA_ENV) python

# Target and sources
TARGET = projection_method
SOURCES = $(SRC_DIR)/main.cpp $(SRC_DIR)/projection_method.cpp $(SRC_DIR)/file_io_improved.cpp
C_SOURCES = $(C_SRC_DIR)/projection_c.c
HEADERS = $(SRC_DIR)/projection_method.h $(SRC_DIR)/cnpy_simple.h $(C_SRC_DIR)/projection_c.h
OBJECTS = $(BUILD_DIR)/main.o $(BUILD_DIR)/projection_method.o $(BUILD_DIR)/file_io_improved.o $(BUILD_DIR)/projection_c.o

.PHONY: all clean run test

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

help:
	@echo "Available targets:"
	@echo "  all         - Build the project (default)"
	@echo "  clean       - Remove build artifacts"
	@echo "  run         - Build and run with default parameters"
	@echo "  test        - Build, run, and validate output"
	@echo ""
	@echo "Example:"
	@echo "  make test"
