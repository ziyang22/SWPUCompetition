#!/bin/bash
# Quick compilation test script
# Updated for new directory structure

echo "Testing C++ compilation..."
echo ""

# Test with improved file_io
echo "Compiling with file_io_improved.cpp..."
g++ -std=c++17 -O3 -Icpp_src -o projection_method cpp_src/main.cpp cpp_src/projection_method.cpp cpp_src/file_io_improved.cpp 2>&1

if [ $? -eq 0 ]; then
    echo "✓ Compilation successful!"
    echo ""
    echo "Executable created: projection_method"
    echo ""
    echo "To run:"
    echo "  ./projection_method"
    echo ""
    echo "To run with custom parameters:"
    echo "  ./projection_method 1.0 0.025 3300 3400 0.5"
else
    echo "✗ Compilation failed"
    exit 1
fi
