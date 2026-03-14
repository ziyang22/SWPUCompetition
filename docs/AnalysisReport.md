# 性能分析报告

本文档记录投影法井眼通过能力计算项目的性能优化过程、benchmark 数据以及各版本的阶段占比分析。

## 1. 最新性能数据

### 1.1 最新长区间实测（3300m → 3400m，step=0.5）

| 指标 | 值 |
|------|------|
| 总耗时 | `0.75s` |
| OpenMP | enabled, 12 线程 |
| 窗口数 | 200 |
| 总方向数 | 34732 |
| 平均每窗口方向数 | 173.66 |

### 1.2 各阶段占比

| 阶段 | 耗时 (s) | 占比 |
|------|----------:|------:|
| max_inscribed_circle | 0.59 | **78.76%** |
| get_closest_points | 0.14 | **18.05%** |
| direction_loop (累计) | 0.75 | 99.95% |
| line_plane_multiple | 0.01 | 1.00% |
| point3d_to_2d | 0.01 | 0.74% |
| mean_reduction | 0.00 | 0.45% |
| residual | 0.01 | 0.94% |
| direction_generation | 0.00 | 0.04% |
| setup | 0.00 | 0.00% |

**结论：**
- `max_inscribed_circle()` 是绝对主热点，占近 **79%** 的计算时间
- `get_closest_points()` 是第二梯队，占约 **18%**
- 其它阶段合计不足 5%

---

## 2. 性能对比

### 2.1 不同构建配置对比

| 版本 | 配置 | 平均耗时 (s) | 相对串行加速比 |
|------|------|-------------:|--------------:|
| Python 原始实现 | - | `226.99s` | 1.0x (基线) |
| CLI 串行 | 默认 `make` | `1.317s` | ~172x |
| CLI + SIMD | `make USE_SIMD=1` | `0.750s` | ~303x |
| CLI + OpenMP + SIMD | `make USE_OPENMP=1 USE_SIMD=1` | `0.620s` | ~366x |
| 最新 CLI 实跑 | OpenMP 12 线程 | `0.75s` | ~303x |

### 2.2 相对 Python 基线的加速比

- 最新 OpenMP + SIMD CLI 相对原始 Python：**约 302x**（0.75s vs 226.99s）
- 历史最佳记录（0.62s）相对原始 Python：**约 366x**

---

## 3. 优化历程

### 3.1 阶段划分

| 阶段 | 主要内容 | 收益 |
|------|----------|------|
| Stage 1-2 | 初始 Python 实现 | 基线 |
| Stage 3 | 纯 C 计算核心移植 | 从 Python 354s → C++ 2.65s，约 134x |
| Stage 4 | OpenMP 并行优化 | C++ 2.65s → ~0.7s，约 3.8x |
| Stage 5 (当前) | 平方距离 + SIMD + OpenMP | 最终 ~0.62-0.75s，约 300x+ |

### 3.2 关键优化点

1. **纯 C 核心** (`c_src/projection_c.c`)
   - 将 Python 算法移植为纯 C 实现
   - 保持与 Python 版本结果一致

2. **OpenMP 并行化** (`c_src/projection_c.c:432-493`)
   - 对 `max_inscribed_circle()` 网格搜索做并行化
   - 使用线程局部最优 + critical 合并
   - 保持 tie-break 规则一致性

3. **平方距离优化** (`c_src/projection_c.c`)
   - 将 `sqrt` 延迟到最终写入候选半径时
   - 内层循环只比较平方距离，减少高频 `sqrt` 调用

4. **SIMD 向量化** (`c_src/projection_c.c`)
   - 为 `min_distance_squared()` 添加 AVX2 向量化路径
   - 每次并行处理 4 个点的距离计算
   - 保留标量 fallback

---

## 4. 热点分析

### 4.1 主热点：`max_inscribed_circle()`

- **占比**：约 75-79%
- **优化措施**：
  - OpenMP 并行网格搜索
  - 平方距离比较
  - SIMD 向量化
- **效果**：仍是最主要瓶颈，但占比已从早期 90%+ 压缩到 79%

### 4.2 次热点：`get_closest_points()`

- **占比**：约 18-21%
- **优化措施**：当前为串行，在主热点进一步优化后可考虑
- **效果**：随主热点占比下降，该阶段相对重要性上升

### 4.3 非热点

- `line_plane_multiple`、`point3d_to_2d`、`mean_reduction`、`direction_generation` 合计不足 3%
- 现阶段不建议投入复杂优化

---

## 5. 验证结果

### 5.1 结果一致性

| 对比项 | 深度差异 (m) | 半径差异 (m) |
|--------|-------------|--------------|
| C++ vs Python | 0.000000 | 0.000000 |
| C vs Python | 0.000000 | 0.000000 |
| OpenMP vs 串行 | 0.000000 | 0.000000 |

### 5.2 构建验证

- ✅ 默认串行构建：`make`
- ✅ OpenMP 构建：`make USE_OPENMP=1`
- ✅ SIMD 构建：`make USE_SIMD=1`
- ✅ OpenMP + SIMD 构建：`make USE_OPENMP=1 USE_SIMD=1`
- ✅ Python 绑定：`pip install -e .`

---

## 6. 相关文件

- 核心实现：`c_src/projection_c.c`
- 构建配置：`Makefile`
- Python 绑定：`cpp_src/python_bindings/`
- 测试脚本：`scripts/test_cpp_binding.py`
- 阶段文档：
  - `docs/STAGE3_C_PORT_SUMMARY.md`
  - `docs/STAGE4_OPENMP_SUMMARY.md`
  - `docs/OPENMP_BENCHMARK_REPORT.md`
