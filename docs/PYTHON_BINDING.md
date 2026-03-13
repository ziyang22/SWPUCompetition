# Python 绑定使用指南

## 安装

在 conda 环境中安装 C++ Python 绑定：

```bash
conda activate SWPUCompetiton
cd cpp_src/python_bindings
pip install -e .

# 返回仓库根目录再运行示例
cd ../..
python examples/use_cpp_binding.py
```

## 使用方法

### 基本用法

Python 绑定现在提供两个兼容 `Projection2` 的后端接口：
- `Projection2_cpp(...)`：现有 C++ 适配路径
- `Projection2_c(...)`：新的纯 C 计算核心路径

C++ 绑定提供了与原始 Python 函数完全兼容的接口：

```python
import numpy as np
import pandas as pd
from projection_cpp import Projection2_c, Projection2_cpp

# 加载数据
all_data = pd.read_csv('data/default/all_data.csv')
Point_3D = np.load('data/default/Point_3D.npy')

# 调用 C++ 实现（接口与 Projection2 完全相同）
deep, R, rr, dd, p_all, t_all, draw_R = Projection2_cpp(
    all_data,           # pandas DataFrame
    Point_3D,           # numpy array
    1.0,                # instrument_length
    0.025,              # instrument_radius
    3300,               # begin_deep
    3400,               # end_deep
    0.5                 # num_step
)

print(f"卡点深度: {deep:.3f} m")
print(f"最小半径: {R:.6f} m")
print(f"最大通过直径: {R * 2 * 1000:.3f} mm")
print(f"总耗时: {t_all:.3f} 秒")
```

### 替换现有代码

如果你已经有使用 `Projection2` 的代码，只需要修改导入语句：

**原始代码：**
```python
from TouYingFa import Projection2

deep, R, rr, dd, p_all, t_all, draw_R = Projection2(
    all_data, Point_3D, instrument_length, instrument_Radius,
    begin_deep, end_deep, num_step
)
```

**使用 C++ 加速：**
```python
from projection_cpp import Projection2_cpp

# 或使用 C 后端
from projection_cpp import Projection2_c

deep, R, rr, dd, p_all, t_all, draw_R = Projection2_cpp(
    all_data, Point_3D, instrument_length, instrument_Radius,
    begin_deep, end_deep, num_step
)
```

### 参数说明

- `all_data`: pandas DataFrame，包含井眼轨迹数据（DEPTH, N, E, H 列）
- `Point_3D`: numpy array，形状为 (depth_points, 24, 3) 的 3D 井壁坐标
- `instrument_length`: 工具长度（米），默认 1.0
- `instrument_radius`: 工具半径（米），默认 0.025
- `begin_deep`: 起始深度（米），默认 None（从头开始）
- `end_deep`: 截止深度（米），默认 None（到底部）
- `num_step`: 步长（米），默认 0.5
- `if_draw`: 与原始 Python 接口兼容的保留参数，默认 False；当前 C++/C 后端忽略绘图输出

### 返回值

返回一个包含 7 个元素的元组：

1. `deep`: 卡点深度或最小半径所在深度（米）
2. `R`: 最小半径（米）
3. `rr`: 所有窗口的半径列表（当前为空列表）
4. `dd`: 通过方向列表（当前为空列表）
5. `p_all`: 窗口平面中心列表（当前为空列表）
6. `t_all`: 总计算时间（秒）
7. `draw_R`: 绘图数据（当前为空列表）

### 输出文件

计算结果会自动保存到 `output/` 目录：

**如果工具能通过：**
- `output/pass_last_5m_{end_deep}m.txt`: 最后 5 米的数据

**如果工具卡住：**
- `output/stuck_point_{depth}m.txt`: 卡点前 5 米的数据
- `output/final_result_{depth}m.txt`: 最终结果摘要

## 性能对比

最近一次在 WSL + `SWPUCompetiton` 环境中的长区间实测（`3300m -> 3400m`，`step=0.5`）可作为当前版本的参考：

- **Python 原始实现**: `226.99s`
- **最新 CLI（OpenMP + SIMD）**: `0.69s`
- **端到端加速比**: 约 **329x**

同一轮 CLI benchmark 中，热点优化后的不同构建配置平均结果为：

- **串行基线**: `1.317s`
- **SIMD**: `0.750s`（总耗时约 `1.76x` 加速）
- **OpenMP + SIMD**: `0.620s`（总耗时约 `2.12x` 加速）

说明：
- Python 绑定路径的最终耗时还会受到 Python 调用链、数据转换和绑定层开销影响
- 若关注纯计算核心的极限吞吐，CLI 路径更能反映 C/C++ 后端的真实收益
- 绑定层的具体速度请以 `scripts/test_cpp_binding.py` 在当前机器上的实测为准

## 示例代码

完整示例请参考：
- `examples/use_cpp_binding.py`: 基本使用示例
- `scripts/test_cpp_binding.py`: 测试和性能对比

## 注意事项

1. **数据格式**: 确保输入数据格式正确（DataFrame 和 NumPy 数组）
2. **输出目录**: 确保 `output/` 目录存在
3. **步长限制**: `num_step` 必须小于 `instrument_length`
4. **深度范围**: `begin_deep` 必须小于 `end_deep`

## 故障排除

### 导入错误

如果遇到 `ImportError: No module named 'projection_cpp'`：

```bash
cd cpp_src/python_bindings
pip install -e .
```

### 编译错误

如果编译失败，检查：
1. 是否安装了 pybind11: `pip install pybind11`
2. 是否有 C++ 编译器: `g++ --version`
3. Python 版本是否 >= 3.8

### 运行时错误

如果运行时出错：
1. 检查数据文件路径是否正确
2. 检查数据格式是否符合要求
3. 查看详细错误信息

## 与原始实现的差异

1. **输出文件位置**: C++ 版本统一保存到 `output/` 目录，Python 版本保存到根目录
2. **返回值**: `rr`, `dd`, `p_all`, `draw_R` 当前返回空列表（核心结果 `deep` 和 `R` 完全一致）
3. **性能**: 当前版本建议参考最新 benchmark 文档；最近一次长区间端到端实测中，最新 CLI 相对原始 Python 约快 **329 倍**

## 下一步

- 查看 `CLAUDE.md` 了解项目整体结构
- 查看 `docs/README.md` 了解算法详情
- 运行 `scripts/test_cpp_binding.py` 进行测试
