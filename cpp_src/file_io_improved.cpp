#include "projection_method.h"
#include "cnpy_simple.h"
#include <fstream>
#include <sstream>
#include <iostream>
#include <iomanip>
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

std::vector<std::vector<Point3D>> loadPoint3DFromNPY(const std::string& filename) {
    std::cout << "正在加载 NPY 文件: " << filename << std::endl;

    // Use the simple NPY loader
    auto npy_array = cnpy_simple::load_npy_double(filename);

    if (npy_array.shape.size() != 3) {
        throw std::runtime_error("NPY 文件必须是 3D 数组");
    }

    size_t dim1 = npy_array.shape[0];  // depth points (37760)
    size_t dim2 = npy_array.shape[1];  // circumferential points (24)
    size_t dim3 = npy_array.shape[2];  // xyz coordinates (3)

    std::cout << "加载3D点数据: (" << dim1 << ", " << dim2 << ", " << dim3 << ")" << std::endl;

    if (dim3 != 3) {
        throw std::runtime_error("第三维度必须是 3 (x, y, z 坐标)");
    }

    // Convert to 2D vector structure
    // point_3d[i][j] is a Point3D
    // This matches Python's Point_3D[i, j, :] which is a single point
    std::vector<std::vector<Point3D>> point_3d(dim1);

    for (size_t i = 0; i < dim1; ++i) {
        point_3d[i].resize(dim2);
        for (size_t j = 0; j < dim2; ++j) {
            point_3d[i][j].x = cnpy_simple::get_3d(npy_array, i, j, 0);
            point_3d[i][j].y = cnpy_simple::get_3d(npy_array, i, j, 1);
            point_3d[i][j].z = cnpy_simple::get_3d(npy_array, i, j, 2);
        }
    }

    std::cout << "NPY 文件加载完成" << std::endl;
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
