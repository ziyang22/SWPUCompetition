# 快速运行指南

本文档按模块/版本提供运行流程，帮助用户快速选择并运行适合自己需求的版本。

---

## 1. 环境准备

### 1.1 WSL + Conda 环境

```bash
# 激活 conda 环境（后续所有命令都需要先执行此步骤）
conda activate SWPUCompetiton

# 如果没有该环境，创建它
conda create -n SWPUCompetiton python=3.8 -y
conda activate SWPUCompetiton
pip install numpy pandas matplotlib scipy pybind11
```

### 1.2 数据文件

项目使用 `data/default/` 目录下的数据：
- `all_data.csv` - 井眼轨迹数据（37761 个点）
- `Point_3D.npy` - 3D 井壁点云数据

---

## 2. Python 原始版本

适用于需要可视化、调试或快速修改算法的场景。

### 编译/运行

```bash
# 直接运行（使用默认参数）
python python_src/TouYingFa.py
```

### 参数设置

修改 `python_src/TouYingFa.py` 底部的参数：

```python
instrument_length = 1.0      # 工具长度 (m)
instrument_Radius = 0.025    # 工具半径 (m)
begin_deep = 3300            # 起始深度 (m)
end_deep = 3400              # 截止深度 (m)
num_step = 0.5               # 步长 (m)
```

### 输出文件

- `pass_last_5m_{depth}m.txt` - 最后 5 米数据
- `stuck_point_{depth}m.txt` - 卡点前 5 米数据（如卡住）
- `final_result_{depth}m.txt` - 卡点摘要（如卡住）

---

## 3. CLI 串行版本

适用于需要快速运行、不需要并行加速的场景。

### 编译

```bash
make clean && make
```

### 运行

```bash
# 命令行模式（使用默认数据集）
./projection_method 1.0 0.025 3300 3400 0.5
# 参数：<工具长度> <工具半径> <起始深度> <截止深度> <步长>

# 交互式模式
./projection_method
```

### 验证

```bash
python scripts/check_output.py
```

---

## 4. CLI OpenMP 版本

适用于需要多核并行加速的场景（需要安装 OpenMP 库）。

### macOS 安装 OpenMP

```bash
brew install libomp
```

### 编译

```bash
make clean && make USE_OPENMP=1
```

### 运行

```bash
# 指定线程数（可选，默认使用系统所有核心）
OMP_NUM_THREADS=8 ./projection_method 1.0 0.025 3300 3400 0.5
```

### 查看热点摘要

程序会自动输出各阶段占比：

```
C 后端热点摘要:
  总耗时: 0.75s
  OpenMP: enabled, 线程数: 12
  max_inscribed_circle: 0.59s (78.76%)
  get_closest_points: 0.14s (18.05%)
  ...
```

---

## 5. CLI SIMD 版本

适用于需要 SIMD 向量化加速的场景（需要支持 AVX2 的 CPU）。

### 编译

```bash
make clean && make USE_SIMD=1
```

### 运行

```bash
./projection_method 1.0 0.025 3300 3400 0.5
```

### 说明

- SIMD 版本会自动检测 CPU 是否支持 AVX2
- 不支持时会自动回退到标量路径
- Apple Silicon (arm64) 会跳过 AVX2 标志，使用标量 fallback

---

## 6. CLI OpenMP + SIMD 版本（推荐）

适用于需要最佳性能的场景，结合多核并行和 SIMD 向量化。

### 编译

```bash
make clean && make USE_OPENMP=1 USE_SIMD=1
```

### 运行

```bash
# 使用全部 CPU 核心
./projection_method 1.0 0.025 3300 3400 0.5

# 或指定线程数
OMP_NUM_THREADS=8 ./projection_method 1.0 0.025 3300 3400 0.5
```

### 性能

| 配置 | 平均耗时 |
|------|----------:|
| 串行 | 1.317s |
| SIMD | 0.750s |
| OpenMP + SIMD | 0.620-0.75s |

---

## 7. Python 绑定版本

适用于在 Python 代码中调用高性能 C/C++ 计算核心的场景。

### 安装

```bash
cd cpp_src/python_bindings
pip install -e .
cd ../..
```

### 运行示例

```python
import numpy as np
import pandas as pd
from projection_cpp import Projection2_cpp, Projection2_c

# 加载数据
all_data = pd.read_csv('data/default/all_data.csv')
Point_3D = np.load('data/default/Point_3D.npy')

# 调用 C++ 版本
deep, R, rr, dd, p_all, t_all, draw_R = Projection2_cpp(
    all_data, Point_3D, 1.0, 0.025, 3300, 3400, 0.5
)

print(f"卡点深度: {deep:.3f} m")
print(f"最小半径: {R:.6f} m")
print(f"计算时间: {t_all:.3f} s")
```

### 两个后端区别

- `Projection2_cpp()`: C++ 适配路径
- `Projection2_c()`: 纯 C 计算核心路径

两者结果一致，性能相近。

### OpenMP Python 绑定

```bash
# 重新安装 OpenMP 版本
cd cpp_src/python_bindings
PROJECTION_USE_OPENMP=1 pip install -e . --force-reinstall --no-deps
cd ../..
```

---

## 8. 验证输出正确性

### 方式 1：使用验证脚本

```bash
python scripts/check_output.py
```

### 方式 2：手动对比

```bash
# 对比特定输出文件
python scripts/compare_cpp_py.py output/pass_last_5m_3400m.txt data/PassedExample/pass_last_5m_3400m.txt
```

---

## 9. 快速选择指南

| 需求 | 推荐版本 |
|------|----------|
| 第一次尝试 | CLI 串行版本 (`make`) |
| 最优性能 | CLI OpenMP+SIMD (`make USE_OPENMP=1 USE_SIMD=1`) |
| Python 中使用 | Python 绑定 (`pip install -e .`) |
| 调试/可视化 | Python 原始版本 (`python python_src/TouYingFa.py`) |
| 只用单核 | CLI 串行版本 (`make`) |

---

## 10. 常见问题

### Q: 编译失败

```bash
# 检查编译器
g++ --version

# 清理后重新编译
make clean && make
```

### Q: 运行结果不一致

```bash
# 验证正确性
python scripts/check_output.py
```

### Q: OpenMP 不可用

- macOS: `brew install libomp`
- Linux: 大多数发行版已自带

### Q: SIMD 不可用

- SIMD 需要 AVX2 支持的 CPU
- 不支持时会自动回退到标量
- Apple Silicon 使用标量路径

---

## 11. 相关文档

- 性能分析报告：`docs/AnalysisReport.md`
- 算法工作流程：`docs/WorkFlow.md`
- 完整 README：`docs/README.md`
- Python 绑定指南：`docs/PYTHON_BINDING.md`