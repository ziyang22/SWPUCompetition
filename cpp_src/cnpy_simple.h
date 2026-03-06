// cnpy_simple.h - Simplified NPY file reader
// For full-featured NPY support, use the cnpy library: https://github.com/rogersce/cnpy

#ifndef CNPY_SIMPLE_H
#define CNPY_SIMPLE_H

#include <vector>
#include <string>
#include <fstream>
#include <stdexcept>
#include <cstdint>
#include <cstring>

namespace cnpy_simple {

// Simple structure to hold NPY array data
template<typename T>
struct NpyArray {
    std::vector<T> data;
    std::vector<size_t> shape;
    size_t word_size;

    size_t num_elements() const {
        size_t n = 1;
        for (size_t s : shape) n *= s;
        return n;
    }
};

// Parse NPY header to extract shape information
inline std::vector<size_t> parse_npy_header(std::ifstream& file) {
    // Read magic string
    char magic[6];
    file.read(magic, 6);

    if (magic[0] != '\x93' || magic[1] != 'N' || magic[2] != 'U' ||
        magic[3] != 'M' || magic[4] != 'P' || magic[5] != 'Y') {
        throw std::runtime_error("Invalid NPY file: bad magic string");
    }

    // Read version
    uint8_t major_version, minor_version;
    file.read(reinterpret_cast<char*>(&major_version), 1);
    file.read(reinterpret_cast<char*>(&minor_version), 1);

    // Read header length
    uint16_t header_len = 0;
    if (major_version == 1) {
        file.read(reinterpret_cast<char*>(&header_len), 2);
    } else if (major_version == 2) {
        uint32_t header_len_32;
        file.read(reinterpret_cast<char*>(&header_len_32), 4);
        header_len = static_cast<uint16_t>(header_len_32);
    } else {
        throw std::runtime_error("Unsupported NPY version");
    }

    // Read header
    std::vector<char> header(header_len);
    file.read(header.data(), header_len);
    std::string header_str(header.begin(), header.end());

    // Parse shape from header
    // Format: {'descr': '<f8', 'fortran_order': False, 'shape': (37760, 24, 3), }
    std::vector<size_t> shape;

    size_t shape_start = header_str.find("'shape': (");
    if (shape_start == std::string::npos) {
        shape_start = header_str.find("\"shape\": (");
    }

    if (shape_start != std::string::npos) {
        size_t shape_end = header_str.find(')', shape_start);
        std::string shape_str = header_str.substr(shape_start + 10, shape_end - shape_start - 10);

        // Parse comma-separated dimensions
        size_t pos = 0;
        while (pos < shape_str.length()) {
            size_t comma = shape_str.find(',', pos);
            if (comma == std::string::npos) comma = shape_str.length();

            std::string dim_str = shape_str.substr(pos, comma - pos);
            // Remove whitespace
            dim_str.erase(0, dim_str.find_first_not_of(" \t"));
            dim_str.erase(dim_str.find_last_not_of(" \t") + 1);

            if (!dim_str.empty()) {
                shape.push_back(std::stoull(dim_str));
            }

            pos = comma + 1;
        }
    }

    return shape;
}

// Load NPY file (double precision)
inline NpyArray<double> load_npy_double(const std::string& filename) {
    std::ifstream file(filename, std::ios::binary);
    if (!file.is_open()) {
        throw std::runtime_error("Cannot open file: " + filename);
    }

    NpyArray<double> array;
    array.shape = parse_npy_header(file);
    array.word_size = sizeof(double);

    // Calculate total number of elements
    size_t num_elements = 1;
    for (size_t s : array.shape) {
        num_elements *= s;
    }

    // Read data
    array.data.resize(num_elements);
    file.read(reinterpret_cast<char*>(array.data.data()), num_elements * sizeof(double));

    if (!file) {
        throw std::runtime_error("Error reading data from NPY file");
    }

    file.close();
    return array;
}

// Helper function to access 3D array data
inline double get_3d(const NpyArray<double>& array, size_t i, size_t j, size_t k) {
    if (array.shape.size() != 3) {
        throw std::runtime_error("Array is not 3D");
    }

    size_t idx = i * array.shape[1] * array.shape[2] + j * array.shape[2] + k;
    return array.data[idx];
}

} // namespace cnpy_simple

#endif // CNPY_SIMPLE_H
