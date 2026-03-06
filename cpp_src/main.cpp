#include "projection_method.h"
#include <iostream>
#include <iomanip>
#include <vector>
#include <string>
#include <dirent.h>
#include <sys/stat.h>

// Check if file exists
bool fileExists(const std::string& path) {
    struct stat buffer;
    return (stat(path.c_str(), &buffer) == 0);
}

// Check if path is a directory
bool isDirectory(const std::string& path) {
    struct stat buffer;
    if (stat(path.c_str(), &buffer) != 0) return false;
    return S_ISDIR(buffer.st_mode);
}

// List available datasets in data/ directory
std::vector<std::string> listDatasets() {
    std::vector<std::string> datasets;
    std::string data_dir = "data";

    if (!isDirectory(data_dir)) {
        return datasets;
    }

    DIR* dir = opendir(data_dir.c_str());
    if (!dir) return datasets;

    struct dirent* entry;
    while ((entry = readdir(dir)) != nullptr) {
        std::string name = entry->d_name;
        if (name == "." || name == "..") continue;

        std::string subdir_path = data_dir + "/" + name;
        if (!isDirectory(subdir_path)) continue;

        std::string csv_path = subdir_path + "/all_data.csv";
        std::string npy_path = subdir_path + "/Point_3D.npy";

        // Check if both required files exist
        if (fileExists(csv_path) && fileExists(npy_path)) {
            datasets.push_back(name);
        }
    }

    closedir(dir);
    return datasets;
}

// Interactive dataset selection
std::string selectDataset() {
    auto datasets = listDatasets();

    if (datasets.empty()) {
        std::cout << "未找到可用数据集，使用当前目录下的数据文件" << std::endl;
        return ".";
    }

    std::cout << "可用数据集:" << std::endl;
    for (size_t i = 0; i < datasets.size(); ++i) {
        std::cout << "  " << (i + 1) << ". " << datasets[i] << std::endl;
    }

    int choice = 0;
    std::cout << "请选择数据集 (1-" << datasets.size() << "): ";
    std::cin >> choice;

    if (choice < 1 || choice > static_cast<int>(datasets.size())) {
        std::cout << "无效选择，使用第一个数据集" << std::endl;
        choice = 1;
    }

    return "data/" + datasets[choice - 1];
}

// Get calculation parameters interactively
void getParameters(double& instrument_length, double& instrument_radius,
                   double& begin_deep, double& end_deep, double& num_step) {
    std::cout << "\n请输入计算参数（直接回车使用默认值）:" << std::endl;

    std::string input;
    std::cin.ignore(); // Clear newline from previous input

    std::cout << "工具长度 (m) [" << instrument_length << "]: ";
    std::getline(std::cin, input);
    if (!input.empty()) instrument_length = std::stod(input);

    std::cout << "工具半径 (m) [" << instrument_radius << "]: ";
    std::getline(std::cin, input);
    if (!input.empty()) instrument_radius = std::stod(input);

    std::cout << "起始深度 (m) [" << begin_deep << "]: ";
    std::getline(std::cin, input);
    if (!input.empty()) begin_deep = std::stod(input);

    std::cout << "截止深度 (m) [" << end_deep << "]: ";
    std::getline(std::cin, input);
    if (!input.empty()) end_deep = std::stod(input);

    std::cout << "步长 (m) [" << num_step << "]: ";
    std::getline(std::cin, input);
    if (!input.empty()) num_step = std::stod(input);
}

int main(int argc, char* argv[]) {
    try {
        std::cout << "=== 井眼通过能力计算程序 (C++ 版本) ===" << std::endl;
        std::cout << std::endl;

        // Determine dataset path
        std::string dataset_path;
        if (argc >= 6) {
            // Command line mode: use default dataset
            dataset_path = "data/default";
            if (!isDirectory(dataset_path)) {
                dataset_path = "."; // Fallback to current directory
            }
        } else {
            // Interactive mode: select dataset
            dataset_path = selectDataset();
        }

        // Load data
        std::cout << "\n正在加载数据..." << std::endl;
        std::string csv_path = dataset_path + "/all_data.csv";
        std::string npy_path = dataset_path + "/Point_3D.npy";

        auto trajectory = projection::loadTrajectoryFromCSV(csv_path);
        auto point_3d = projection::loadPoint3DFromNPY(npy_path);

        // Configuration parameters
        double instrument_length = 1.0;      // 工具长度 (m)
        double instrument_radius = 0.025;    // 工具半径 (m)
        double begin_deep = 3300.0;          // 起始深度 (m)
        double end_deep = 3400.0;            // 截止深度 (m)
        double num_step = 0.5;               // 步长 (m)

        // Parse command line arguments if provided
        if (argc >= 6) {
            instrument_length = std::stod(argv[1]);
            instrument_radius = std::stod(argv[2]);
            begin_deep = std::stod(argv[3]);
            end_deep = std::stod(argv[4]);
            num_step = std::stod(argv[5]);
        } else {
            // Interactive mode: get parameters
            getParameters(instrument_length, instrument_radius, begin_deep, end_deep, num_step);
        }

        std::cout << std::endl;
        std::cout << "计算参数:" << std::endl;
        std::cout << "  工具长度: " << instrument_length << " m" << std::endl;
        std::cout << "  工具半径: " << instrument_radius << " m" << std::endl;
        std::cout << "  起始深度: " << begin_deep << " m" << std::endl;
        std::cout << "  截止深度: " << end_deep << " m" << std::endl;
        std::cout << "  步长: " << num_step << " m" << std::endl;
        std::cout << std::endl;

        // Create calculator
        projection::ProjectionCalculator calculator(
            trajectory,
            point_3d,
            instrument_length,
            instrument_radius,
            num_step
        );

        // Run calculation
        std::cout << "开始计算..." << std::endl;
        std::cout << std::string(60, '=') << std::endl;

        std::vector<projection::CalculationResult> results;
        double stuck_depth = 0.0;
        double min_radius = 0.0;

        bool passed = calculator.calculate(
            begin_deep,
            end_deep,
            results,
            stuck_depth,
            min_radius
        );

        std::cout << std::string(60, '=') << std::endl;
        std::cout << std::endl;

        // Print summary
        if (passed) {
            std::cout << "✓ 工具可以通过!" << std::endl;
            std::cout << "  工具长度: " << std::fixed << std::setprecision(3)
                      << instrument_length << " m" << std::endl;
            std::cout << "  工具半径: " << instrument_radius << " m" << std::endl;
            std::cout << "  工具直径: " << instrument_radius * 2.0 * 1000.0 << " mm" << std::endl;
        } else {
            std::cout << "✗ 工具无法通过!" << std::endl;
            std::cout << "  工具长度: " << std::fixed << std::setprecision(3)
                      << instrument_length << " m" << std::endl;
            std::cout << "  最大通过直径: " << min_radius * 2.0 * 1000.0 << " mm" << std::endl;
            std::cout << "  卡点深度: " << stuck_depth << " m" << std::endl;
        }

        std::cout << std::endl;
        std::cout << "计算完成!" << std::endl;

        return passed ? 0 : 1;

    } catch (const std::exception& e) {
        std::cerr << "错误: " << e.what() << std::endl;
        return 1;
    }
}
