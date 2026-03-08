# SWPU Competition - 井眼通过能力计算

投影法算法实现，用于计算钻井工具在井眼中的通过能力。

## 📁 项目结构

```
.
├── cpp_src/              # C++ 源代码
│   ├── python_bindings/ # Python 绑定 (pybind11)
│   ├── projection_method.h
│   ├── projection_method.cpp
│   ├── file_io_improved.cpp
│   ├── cnpy_simple.h
│   └── main.cpp
├── python_src/           # Python 源代码
│   └── TouYingFa.py
├── data/                 # 数据集目录
│   ├── default/         # 默认数据集
│   ├── PassedExample/   # 通过示例
│   └── FailedExample/   # 失败示例
├── output/              # 输出文件目录
├── scripts/             # Python 和 Shell 脚本
│   ├── check_output.py
│   ├── compare_cpp_py.py
│   ├── benchmark.py
│   ├── test_cpp_binding.py
│   ├── build_and_test.sh
│   └── test_compile.sh
├── examples/            # 使用示例
│   └── use_cpp_binding.py
├── docs/                # 文档
│   ├── README.md
│   ├── PYTHON_BINDING.md
│   ├── QUICK_START.md
│   ├── COMPILE_GUIDE.md
│   ├── HOW_TO_USE.md
│   └── QUICK_REFERENCE.md
├── build/               # 构建目录
├── Makefile             # Makefile 配置
└── CLAUDE.md            # Claude Code 指南
```

## 🚀 快速开始

### 方式 1: C++ 独立程序（交互式，推荐）

```bash
make                    # 编译
./projection_method     # 交互式选择数据集和参数
```

### 方式 2: C++ 命令行运行

```bash
make
./projection_method 1.0 0.025 3300 3400 0.5  # 使用默认数据集
```

### 方式 3: Python 调用 C++ / C 后端

```bash
# 安装 Python 绑定
conda activate SWPUCompetiton
cd cpp_src/python_bindings
pip install -e .

# 在仓库根目录运行示例
cd ../..
python examples/use_cpp_binding.py
```

### 方式 4: 完整测试

```bash
make test              # 编译、运行并验证输出
```

## 📊 性能对比

| 版本 | 计算时间 (100m) | 加速比 |
|------|----------------|--------|
| Python 原始实现 | ~64s | 1x |
| C++ 独立程序 | ~2.65s | **24x** |
| C++ Python 绑定 | ~0.29s | **220x** |

## 🎯 使用示例

### C++ 交互式模式
```bash
./projection_method

# 输出：
# 可用数据集：
#   1. default
#   2. PassedExample
#   3. FailedExample
# 请选择数据集 (1-3): 1
#
# 请输入计算参数（直接回车使用默认值）：
# 工具长度 (m) [1.0]:
# 工具半径 (m) [0.025]:
# ...
```

### C++ 命令行模式
```bash
./projection_method <工具长度> <工具半径> <起始深度> <截止深度> <步长>

# 示例
./projection_method 1.0 0.025 3300 3400 0.5
```

### Python 调用 C++ (推荐)
```python
from projection_cpp import Projection2_c, Projection2_cpp
import pandas as pd
import numpy as np

# 加载数据
all_data = pd.read_csv('data/default/all_data.csv')
Point_3D = np.load('data/default/Point_3D.npy')

# 调用 C++ 实现（220x 加速）
deep, R, rr, dd, p_all, t_all, draw_R = Projection2_cpp(
    all_data, Point_3D, 1.0, 0.025, 3300, 3400, 0.5
)

print(f"最大通过直径: {R * 2 * 1000:.3f} mm")
```

### 验证输出
```bash
python scripts/check_output.py
```

## 📖 文档

- [项目文档](docs/README.md) - 完整项目文档
- [Python 绑定指南](docs/PYTHON_BINDING.md) - C++ Python 绑定使用说明
- [快速开始](docs/QUICK_START.md) - 3 步快速开始
- [使用指南](docs/HOW_TO_USE.md) - 详细使用说明
- [编译指南](docs/COMPILE_GUIDE.md) - 编译选项和故障排除
- [快速参考](docs/QUICK_REFERENCE.md) - 常用命令速查

## 🔧 环境要求

### C++ 独立程序
- C++17 编译器（GCC 7+, Clang 5+, MSVC 2017+）
- Make

### Python 版本 & C++ 绑定
- Python 3.8+
- NumPy, Pandas, Matplotlib, SciPy
- pybind11 (用于 C++ 绑定)
- C++17 编译器（用于编译绑定）

## 📝 输出文件

所有输出文件保存在 `output/` 目录：

### 通过情况
- `output/pass_last_5m_{depth}m.txt` - 最后 5 米的计算数据

### 卡点情况
- `output/stuck_point_{depth}m.txt` - 卡点前 5 米数据
- `output/final_result_{depth}m.txt` - 卡点摘要信息

## 🗂️ 数据集管理

项目支持多数据集切换：

- `data/default/` - 默认数据集（命令行模式使用）
- `data/PassedExample/` - 工具可通过的示例
- `data/FailedExample/` - 工具卡住的示例

每个数据集目录需包含：
- `all_data.csv` - 井眼轨迹数据
- `Point_3D.npy` - 3D 点云数据

## ✅ 验证结果

```
✓ 列 '深度(m)' 一致 (最大差异: 0.0000000000e+00)
✓ 列 '工具长度(m)' 一致 (最大差异: 0.0000000000e+00)
✓ 列 '圆心X(m)' 一致 (最大差异: 0.0000000000e+00)
✓ 列 '圆心Y(m)' 一致 (最大差异: 0.0000000000e+00)
✓ 列 '直径(m)' 一致 (最大差异: 0.0000000000e+00)

🎉 所有文件对比通过！
```

## 🛠️ 常用命令

```bash
# C++ 独立程序
make clean && make      # 清理并重新编译
make test               # 运行测试

# Python 绑定
cd cpp_src/python_bindings
pip install -e .        # 安装 C++ Python 绑定
python ../../examples/use_cpp_binding.py  # 运行示例

# 测试和验证
python scripts/test_cpp_binding.py   # 测试 Python 绑定
python scripts/benchmark.py          # 性能对比
python scripts/check_output.py      # 验证输出
```

## 📦 项目特点

- ✅ 完整的算法移植（与 Python 版本完全一致）
- ✅ 极致的性能（C++ 独立程序 24x，Python 绑定 220x）
- ✅ Python 绑定支持（pybind11，无缝集成）
- ✅ 严格的验证（输出精度完全匹配）
- ✅ 交互式数据集选择
- ✅ 清晰的目录结构
- ✅ 完善的文档
- ✅ 自动化工具

## 📄 许可

SWPU Competition Project

---

**快速链接**：
- 🚀 [快速开始](docs/QUICK_START.md)
- 🐍 [Python 绑定指南](docs/PYTHON_BINDING.md)
- 📖 [完整文档](docs/README.md)
- 🔧 [编译指南](docs/COMPILE_GUIDE.md)
- 📊 [性能对比](scripts/benchmark.py)
