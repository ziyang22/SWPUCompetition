# SWPU Competition - 井眼通过能力计算

投影法算法实现，用于计算钻井工具在井眼中的通过能力。

## 项目简介

本项目实现了基于投影法的井眼通过能力计算算法，可以判断给定尺寸的钻井工具是否能够通过特定井段，并找出卡点位置和最大可通过直径。

**提供两个版本：**
- 🐍 **Python 版本** - 原始实现，支持可视化
- ⚡ **C++ / C 版本** - 高性能实现，最新长区间实测相对原始 Python 约 **329x** 加速

## 快速开始

### C++ 版本（推荐）

```bash
# 编译
make

# 交互式运行（选择数据集）
./projection_method

# 命令行运行（使用默认数据集）
./projection_method 1.0 0.025 3300 3400 0.5

# 验证输出
python scripts/check_output.py
```

### Python 版本

```bash
# 激活 conda 环境
conda activate SWPUCompetiton

# 运行
python python_src/TouYingFa.py

# 验证输出
python scripts/check_output.py
```

详细说明请查看 [QUICK_START.md](QUICK_START.md)

## 环境配置

### Python 环境

```bash
# 创建 conda 环境
conda create -n SWPUCompetiton python=3.8 -y

# 激活环境
conda activate SWPUCompetiton

# 安装依赖
pip install numpy pandas matplotlib scipy
```

### C++ 环境

- C++17 编译器 (GCC 7+, Clang 5+, MSVC 2017+)
- CMake 3.10+ (可选)
- Make (可选)

## 输入数据

- **all_data.csv** - 井眼轨迹数据
  - 包含深度、坐标 (N, E, H)、井斜、方位角等
  - 24 个测量臂的数据 (FING1-FING24)

- **Point_3D.npy** - 井壁 3D 点云数据
  - 形状: (37760, 24, 3)
  - 表示每个深度点的 24 个周向测量点的 xyz 坐标

## 算法原理

投影法通过以下步骤计算通过能力：

1. **滑动窗口** - 按工具长度在井眼中滑动
2. **投影方向** - 生成主轴周围锥形角度范围内的投影方向
3. **平面投影** - 将上平面点投影到下平面
4. **内边界提取** - 找出投影后的内边界点
5. **最大内切圆** - 计算内边界的最大内切圆
6. **通过判断** - 比较工具半径与最大内切圆半径

## 输出文件

### 通过情况
- `pass_last_5m_{depth}m.txt` - 最后 5 米的计算数据

### 卡点情况
- `stuck_point_{depth}m.txt` - 卡点前 5 米数据
- `final_result_{depth}m.txt` - 卡点摘要信息

输出格式：
```
深度(m),工具长度(m),圆心X(m),圆心Y(m),直径(m),当前段耗时(s),总耗时(s)
```

## 项目结构

```
.
├── TouYingFa.py              # Python 实现
├── check_output.py           # 输出验证脚本
├── all_data.csv              # 轨迹数据
├── Point_3D.npy              # 3D 点云数据
├── PassedExample/            # 参考输出
│   └── pass_last_5m_3400m.txt
├── 无法通过示例/             # 卡点示例
│   ├── stuck_point_3393.5m.txt
│   └── final_result_3393.5m.txt
│
├── projection_method.h       # C++ 头文件
├── projection_method.cpp     # C++ 实现
├── file_io_improved.cpp      # 文件 I/O
├── cnpy_simple.h             # NPY 解析器
├── main.cpp                  # C++ 主程序
├── CMakeLists.txt            # CMake 配置
├── Makefile                  # Makefile 配置
│
├── build_and_test.sh         # 自动构建测试
├── test_compile.sh           # 快速编译
├── benchmark.py              # 性能对比
├── compare_cpp_py.py         # 输出对比
│
├── CLAUDE.md                 # Claude Code 指南
├── README_CPP.md             # C++ 版本说明
├── QUICK_START.md            # 快速开始
├── COMPILE_GUIDE.md          # 编译指南
└── CPP_REFACTOR_COMPLETE.md  # 重构总结
```

## 使用示例

### 基本使用

```bash
# Python 版本
python TouYingFa.py

# C++ 版本
./projection_method
```

### 自定义参数

**Python 版本** - 修改 TouYingFa.py 底部的参数：
```python
instrument_length = 1.0      # 工具长度 (m)
instrument_Radius = 0.025    # 工具半径 (m)
begin_deep = 3300            # 起始深度 (m)
end_deep = 3400              # 截止深度 (m)
num_step = 0.5               # 步长 (m)
```

**C++ 版本** - 命令行参数：
```bash
./projection_method 1.0 0.025 3300 3400 0.5
```

### 验证结果

```bash
# 验证输出正确性
python check_output.py

# 对比 C++ 和 Python 输出
python compare_cpp_py.py pass_last_5m_3400m.txt PassedExample/pass_last_5m_3400m.txt

# 性能对比
python benchmark.py
```

## 性能对比

以下数字以最近一次在 WSL + `SWPUCompetiton` 环境中的长区间实测为参考（默认数据集，`3300m -> 3400m`，`step=0.5`）：

| 版本 / 配置 | 计算时间 | 说明 |
|------|---------:|------|
| Python 原始实现 | `226.99s` | 直接调用参考实现 |
| CLI 串行基线 | `1.317s` | C/C++ 原生路径平均值 |
| CLI + SIMD | `0.750s` | 相对串行约 `1.76x` |
| CLI + OpenMP + SIMD | `0.620s` | 相对串行约 `2.12x` |
| 最新一次 CLI 实跑 | `0.69s` | OpenMP 已启用，线程数 12 |

按最近一次端到端对比，**最新版本相对原始 Python 约快 329x**。

说明：
- `max_inscribed_circle()` 仍是主要热点，SIMD 与 OpenMP 的收益主要来自这一段
- Python 绑定路径也能复用同一计算核心，但端到端耗时会额外受 Python/绑定层开销影响
- 若要复现实测，请优先在 WSL 的 `SWPUCompetiton` 环境中运行

## 文档

- [QUICK_START.md](QUICK_START.md) - 快速开始指南
- [README_CPP.md](README_CPP.md) - C++ 版本详细说明
- [COMPILE_GUIDE.md](COMPILE_GUIDE.md) - 编译指南
- [CPP_REFACTOR_COMPLETE.md](CPP_REFACTOR_COMPLETE.md) - 重构总结
- [CLAUDE.md](CLAUDE.md) - Claude Code 使用指南

## 常见问题

### Q: 如何选择 Python 还是 C++ 版本？

- **Python 版本**：需要可视化、调试、快速修改算法
- **C++ 版本**：需要高性能、生产部署、批量计算

### Q: 输出结果是否一致？

是的，两个版本的算法逻辑完全相同，输出结果一致（可通过 `check_output.py` 验证）。

### Q: C++ 版本如何编译？

最简单的方式：
```bash
make
```

详细说明请查看 [COMPILE_GUIDE.md](COMPILE_GUIDE.md)

### Q: 如何修改算法参数？

关键参数位置：
- **投影锥角**: `projection_method.cpp` 第 263 行 `delta = 0.030 / instrument_length_`
- **角度步长**: 第 264 行 `angle_step = delta / 8.0`
- **网格分辨率**: 第 299 行 `maxInscribedCircle(S_P_projection_2d, 30)`

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可

SWPU Competition Project

## 联系方式

如有问题，请查看文档或提交 Issue。

---

**快速链接：**
- 🚀 [快速开始](QUICK_START.md)
- 📖 [C++ 版本说明](README_CPP.md)
- 🔧 [编译指南](COMPILE_GUIDE.md)
- 📊 [性能对比](benchmark.py)
