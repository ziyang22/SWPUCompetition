# C++ 编译指南

## 快速开始

### 最简单的方式

```bash
# 1. 快速编译测试
./test_compile.sh

# 2. 运行
./projection_method_test
```

### 推荐方式：使用 CMake

```bash
mkdir build
cd build
cmake ..
make
./projection_method
```

### 使用 Makefile

```bash
make
./projection_method
```

## 编译选项说明

### 选择 NPY 加载器

项目提供两个文件 I/O 实现：

**file_io.cpp** (简单版):
- 假设固定数据形状
- 无额外依赖
- 适合快速测试

**file_io_improved.cpp** (推荐):
- 自动解析 NPY 头部
- 支持任意形状
- 使用 cnpy_simple.h

#### 修改 CMakeLists.txt

```cmake
# 使用简单版
set(SOURCES main.cpp projection_method.cpp file_io.cpp)

# 或使用改进版（推荐）
set(SOURCES main.cpp projection_method.cpp file_io_improved.cpp)
```

#### 修改 Makefile

```makefile
# 使用简单版
SOURCES = main.cpp projection_method.cpp file_io.cpp

# 或使用改进版（推荐）
SOURCES = main.cpp projection_method.cpp file_io_improved.cpp
```

## 编译器要求

- **最低要求**: C++17
- **推荐编译器**:
  - GCC 7.0+
  - Clang 5.0+
  - MSVC 2017+

### 检查编译器版本

```bash
# GCC
g++ --version

# Clang
clang++ --version
```

## 优化选项

### 基础优化

```bash
g++ -std=c++17 -O3 -o projection_method main.cpp projection_method.cpp file_io_improved.cpp
```

### 启用 OpenMP 并行化

```bash
g++ -std=c++17 -O3 -fopenmp -o projection_method main.cpp projection_method.cpp file_io_improved.cpp
```

### 最大优化（可能需要更长编译时间）

```bash
g++ -std=c++17 -O3 -march=native -flto -o projection_method main.cpp projection_method.cpp file_io_improved.cpp
```

## 平台特定说明

### macOS

```bash
# 使用 Clang
clang++ -std=c++17 -O3 -o projection_method main.cpp projection_method.cpp file_io_improved.cpp

# 或使用 Homebrew GCC
brew install gcc
g++-13 -std=c++17 -O3 -o projection_method main.cpp projection_method.cpp file_io_improved.cpp
```

### Linux

```bash
# Ubuntu/Debian
sudo apt-get install g++ cmake

# CentOS/RHEL
sudo yum install gcc-c++ cmake

# 编译
g++ -std=c++17 -O3 -o projection_method main.cpp projection_method.cpp file_io_improved.cpp
```

### Windows

#### 使用 MinGW

```bash
g++ -std=c++17 -O3 -o projection_method.exe main.cpp projection_method.cpp file_io_improved.cpp
```

#### 使用 MSVC

```bash
cl /std:c++17 /O2 /EHsc main.cpp projection_method.cpp file_io_improved.cpp
```

## 常见编译错误

### 错误 1: "error: 'optional' is not a member of 'std'"

**原因**: 编译器不支持 C++17

**解决**:
```bash
# 确保使用 -std=c++17
g++ -std=c++17 ...
```

### 错误 2: "undefined reference to 'sqrt'"

**原因**: 缺少数学库链接

**解决**:
```bash
g++ ... -lm
```

### 错误 3: "cannot open file 'cnpy_simple.h'"

**原因**: 头文件不在当前目录

**解决**:
```bash
# 确保 cnpy_simple.h 在同一目录
ls cnpy_simple.h

# 或指定包含路径
g++ -I. ...
```

## 验证编译结果

### 1. 检查可执行文件

```bash
ls -lh projection_method
file projection_method
```

### 2. 运行测试

```bash
./projection_method 1.0 0.025 3395 3400 0.5
```

### 3. 对比输出

```bash
python compare_cpp_py.py pass_last_5m_3400m.txt PassedExample/pass_last_5m_3400m.txt
```

## 性能调优

### 1. 编译器优化级别

- `-O0`: 无优化（调试用）
- `-O1`: 基础优化
- `-O2`: 推荐优化
- `-O3`: 最大优化（推荐）

### 2. 特定 CPU 优化

```bash
# 针对当前 CPU 优化
g++ -std=c++17 -O3 -march=native ...

# 针对特定架构
g++ -std=c++17 -O3 -march=skylake ...
```

### 3. 链接时优化 (LTO)

```bash
g++ -std=c++17 -O3 -flto ...
```

### 4. 并行编译

```bash
# 使用 make 并行编译
make -j8

# 使用 CMake 并行编译
cmake --build . -j8
```

## 调试版本

### 编译调试版本

```bash
g++ -std=c++17 -g -O0 -o projection_method_debug main.cpp projection_method.cpp file_io_improved.cpp
```

### 使用 GDB 调试

```bash
gdb ./projection_method_debug
(gdb) run 1.0 0.025 3300 3400 0.5
```

### 使用 Valgrind 检查内存

```bash
valgrind --leak-check=full ./projection_method_debug
```

## 清理构建文件

```bash
# 使用 Makefile
make clean

# 使用 CMake
rm -rf build/

# 手动清理
rm -f *.o projection_method projection_method_test
```

## 完整构建流程示例

```bash
# 1. 克隆或下载项目
cd SWPU-Competition

# 2. 确保数据文件存在
ls all_data.csv Point_3D.npy

# 3. 编译（选择一种方式）
./test_compile.sh
# 或
make
# 或
mkdir build && cd build && cmake .. && make && cd ..

# 4. 运行
./projection_method

# 5. 验证结果
python check_output.py

# 6. 性能对比（可选）
python benchmark.py
```

## 获取帮助

如果遇到编译问题：

1. 检查编译器版本是否支持 C++17
2. 确保所有源文件在同一目录
3. 查看完整的错误信息
4. 尝试使用不同的编译器或优化级别
