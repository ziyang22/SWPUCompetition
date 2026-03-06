#include "projection_method.h"
#include <fstream>
#include <sstream>
#include <iostream>
#include <stdexcept>

namespace projection {

std::vector<TrajectoryPoint> loadTrajectoryFromCSV(const std::string& filename) {
    std::ifstream file(filename);
    if (!file.is_open()) {
        throw std::runtime_error("无法打开文件: " + filename);
    }

    std::vector<TrajectoryPoint> trajectory;
    std::string line;

    // Skip header
    std::getline(file, line);

    while (std::getline(file, line)) {
        std::stringstream ss(line);
        std::string token;
        std::vector<std::string> tokens;

        while (std::getline(ss, token, ',')) {
            tokens.push_back(token);
        }

        if (tokens.size() < 4) continue;

        TrajectoryPoint point;
        point.depth = std::stod(tokens[0]);
        point.position.x = std::stod(tokens[1]);  // N
        point.position.y = std::stod(tokens[2]);  // E
        point.position.z = std::stod(tokens[3]);  // H

        trajectory.push_back(point);
    }

    file.close();
    std::cout << "加载轨迹数据: " << trajectory.size() << " 个点" << std::endl;
    return trajectory;
}

std::vector<std::vector<std::vector<Point3D>>> loadPoint3DFromNPY(const std::string& filename) {
    // This is a simplified NPY loader
    // For production use, consider using a library like cnpy

    std::ifstream file(filename, std::ios::binary);
    if (!file.is_open()) {
        throw std::runtime_error("无法打开文件: " + filename);
    }

    // Read NPY header
    char magic[6];
    file.read(magic, 6);

    if (magic[0] != '\x93' || magic[1] != 'N' || magic[2] != 'U' ||
        magic[3] != 'M' || magic[4] != 'P' || magic[5] != 'Y') {
        throw std::runtime_error("不是有效的NPY文件");
    }

    uint8_t major_version, minor_version;
    file.read(reinterpret_cast<char*>(&major_version), 1);
    file.read(reinterpret_cast<char*>(&minor_version), 1);

    uint16_t header_len;
    file.read(reinterpret_cast<char*>(&header_len), 2);

    std::vector<char> header(header_len);
    file.read(header.data(), header_len);
    std::string header_str(header.begin(), header.end());

    // Parse shape from header (simplified - assumes shape is (37760, 24, 3))
    // For production, parse the header properly
    int dim1 = 37760;
    int dim2 = 24;
    int dim3 = 3;

    std::cout << "加载3D点数据: (" << dim1 << ", " << dim2 << ", " << dim3 << ")" << std::endl;

    std::vector<std::vector<std::vector<Point3D>>> point_3d(dim1);

    for (int i = 0; i < dim1; ++i) {
        point_3d[i].resize(dim2);
        for (int j = 0; j < dim2; ++j) {
            point_3d[i][j].resize(dim3);
            for (int k = 0; k < dim3; ++k) {
                double value;
                file.read(reinterpret_cast<char*>(&value), sizeof(double));

                if (k == 0) point_3d[i][j][k].x = value;
                else if (k == 1) point_3d[i][j][k].y = value;
                else point_3d[i][j][k].z = value;
            }
        }
    }

    file.close();
    return point_3d;
}

void saveResults(const std::string& filename, const std::vector<CalculationResult>& results) {
    std::ofstream file(filename);
    if (!file.is_open()) {
        throw std::runtime_error("无法创建文件: " + filename);
    }

    file << "深度(m),工具长度(m) ,圆心X(m), 圆心Y(m),直径(m) ,当前段耗时(s),总耗时(s)\n";

    for (const auto& result : results) {
        file << std::fixed << std::setprecision(3) << result.depth << ","
             << std::setprecision(6) << result.tool_length << ","
             << result.center_x << "," << result.center_y << ","
             << result.diameter << "," << result.current_time << ","
             << result.total_time << "\n";
    }

    file.close();
}

} // namespace projection
