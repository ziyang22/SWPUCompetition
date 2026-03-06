# 快速开始指南

## 30 秒快速开始

```bash
# 编译
make

# 运行
./projection_method

# 验证
python check_output.py
```

就这么简单！

---

## 详细步骤

### 步骤 1: 准备环境

确保你有：
- ✅ C++17 编译器 (g++ 7+, clang++ 5+)
- ✅ 输入数据文件: `all_data.csv` 和 `Point_3D.npy`
- ✅ Python 3.8+ (用于验证，可选)

检查编译器：
```bash
g++ --version
```

### 步骤 2: 编译程序

**选项 A - 最简单**
```bash
./test_compile.sh
```

**选项 B - 使用 Makefile**
```bash
make
```

**选项 C - 使用 CMake**
```bash
mkdir build && cd build
cmake ..
make
cd ..
```

### 步骤 3: 运行程序

**默认参数**
```bash
./projection_method
```

**自定义参数**
```bash
./projection_method 1.0 0.025 3300 3400 0.5
#                   ↑   ↑     ↑    ↑    ↑
#                   |   |     |    |    步长(m)
#                   |   |     |    截止深度(m)
#                   |   |     起始深度(m)
#                   |   工具半径(m)
#                   工具长度(m)
```

### 步骤 4: 查看结果

程序会生成输出文件：

**如果通过**
- `pass_last_5m_3400m.txt` - 最后 5 米的计算数据

**如果卡住**
- `stuck_point_3393.5m.txt` - 卡点前 5 米数据
- `final_result_3393.5m.txt` - 卡点摘要

### 步骤 5: 验证正确性（可选）

```bash
python check_output.py
```

---

## 常用命令

### 编译相关
```bash
# 清理构建文件
make clean

# 重新编译
make clean && make

# 查看可执行文件信息
file projection_method
ls -lh projection_method
```

### 运行相关
```bash
# 查看帮助（查看参数说明）
./projection_method --help  # 注：当前版本无 --help，直接运行即可

# 运行并保存日志
./projection_method 2>&1 | tee output.log

# 后台运行
nohup ./projection_method > output.log 2>&1 &
```

### 测试相关
```bash
# 验证输出
python check_output.py

# 性能对比
python benchmark.py

# 对比特定文件
python compare_cpp_py.py pass_last_5m_3400m.txt PassedExample/pass_last_5m_3400m.txt
```

---

## 示例场景

### 场景 1: 测试工具是否能通过

```bash
# 编译
make

# 运行：工具长度 1m，半径 0.025m，深度 3300-3400m
./projection_method 1.0 0.025 3300 3400 0.5

# 查看结果
cat pass_last_5m_3400m.txt
```

### 场景 2: 找到卡点位置

```bash
# 使用较大的工具半径
./projection_method 1.0 0.05 3300 3400 0.5

# 查看卡点信息
cat final_result_*.txt
cat stuck_point_*.txt
```

### 场景 3: 性能测试

```bash
# 编译优化版本
g++ -std=c++17 -O3 -march=native -o projection_method main.cpp projection_method.cpp file_io_improved.cpp

# 计时运行
time ./projection_method 1.0 0.025 3300 3400 0.5

# 与 Python 版本对比
python benchmark.py
```

---

## 故障排除

### 问题 1: 编译失败

```bash
# 检查编译器版本
g++ --version

# 如果版本太低，尝试使用 clang++
clang++ -std=c++17 -O3 -o projection_method main.cpp projection_method.cpp file_io_improved.cpp
```

### 问题 2: 找不到输入文件

```bash
# 检查文件是否存在
ls -lh all_data.csv Point_3D.npy

# 确保在正确的目录
pwd
```

### 问题 3: 输出结果不一致

```bash
# 详细对比
python compare_cpp_py.py pass_last_5m_3400m.txt PassedExample/pass_last_5m_3400m.txt

# 检查输入数据是否正确
head -5 all_data.csv
```

### 问题 4: 程序运行很慢

```bash
# 确保使用了优化编译
make clean
CXXFLAGS="-O3 -march=native" make

# 或使用 CMake Release 模式
mkdir build && cd build
cmake -DCMAKE_BUILD_TYPE=Release ..
make
```

---

## 下一步

- 📖 阅读 [README_CPP.md](README_CPP.md) 了解更多细节
- 🔧 查看 [COMPILE_GUIDE.md](COMPILE_GUIDE.md) 学习高级编译选项
- 📊 运行 `python benchmark.py` 查看性能提升
- 🎯 修改参数进行不同场景的测试

---

## 获取帮助

如果遇到问题：

1. 查看 [COMPILE_GUIDE.md](COMPILE_GUIDE.md) 中的常见错误
2. 检查 [CPP_REFACTOR_COMPLETE.md](CPP_REFACTOR_COMPLETE.md) 中的 FAQ
3. 确保所有文件都在同一目录
4. 尝试使用不同的编译器或构建方式

---

**祝使用愉快！** 🚀
