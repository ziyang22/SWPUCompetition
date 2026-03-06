#!/bin/bash

# Build and test script for Projection Method C++ implementation
# Updated for new directory structure

set -e  # Exit on error

echo "=================================="
echo "Projection Method - Build & Test"
echo "=================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if required files exist
echo "Checking required files..."
if [ ! -f "all_data.csv" ]; then
    echo -e "${RED}Error: all_data.csv not found${NC}"
    exit 1
fi

if [ ! -f "Point_3D.npy" ]; then
    echo -e "${RED}Error: Point_3D.npy not found${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Input files found${NC}"
echo ""

# Build using CMake if available, otherwise use Makefile
echo "Building project..."
if command -v cmake &> /dev/null; then
    echo "Using CMake build system..."
    mkdir -p build
    cd build
    cmake .. -DCMAKE_BUILD_TYPE=Release
    make -j$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 2)
    cd ..
    EXECUTABLE="./build/projection_method"
elif command -v make &> /dev/null; then
    echo "Using Makefile..."
    make clean
    make -j$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 2)
    EXECUTABLE="./projection_method"
else
    echo "Using manual compilation..."
    mkdir -p build
    g++ -std=c++17 -O3 -Icpp_src -o projection_method cpp_src/main.cpp cpp_src/projection_method.cpp cpp_src/file_io_improved.cpp
    EXECUTABLE="./projection_method"
fi

echo -e "${GREEN}✓ Build successful${NC}"
echo ""

# Run the program
echo "Running calculation..."
echo "=================================="
$EXECUTABLE 1.0 0.025 3395 3400 0.5

echo ""
echo "=================================="
echo -e "${GREEN}✓ Calculation complete${NC}"
echo ""

# Check if Python is available for validation
if command -v python3 &> /dev/null; then
    echo "Running validation..."
    if [ -f "scripts/check_output.py" ]; then
        python3 scripts/check_output.py
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ Validation passed${NC}"
        else
            echo -e "${YELLOW}⚠ Validation failed - check output differences${NC}"
        fi
    else
        echo -e "${YELLOW}⚠ check_output.py not found, skipping validation${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Python3 not found, skipping validation${NC}"
fi

echo ""
echo "=================================="
echo "Build and test complete!"
echo "=================================="
