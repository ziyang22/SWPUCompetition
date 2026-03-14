# OpenMP 优化 Benchmark 报告

## 1. 报告目的

本报告用于记录纯 C 计算核心在引入 OpenMP 并行优化后的实际 benchmark 结果，并对以下几类实现进行统一验证：

- Python 原始实现
- C++ Python 绑定实现 `Projection2_cpp(...)`
- C Python 绑定实现 `Projection2_c(...)`
- OpenMP 版 C 后端
- CLI 串行版本
- CLI OpenMP 版本

本次重点关注两类指标：

1. **正确性**：不同实现是否给出一致结果
2. **性能**：各实现耗时以及相对 Python 基线/串行 CLI 的加速比

---

## 2. 测试环境

### 2.1 数据与参数

本文档保留了阶段 4 OpenMP benchmark 的历史结论，同时补充后续热点优化（平方距离比较 + 可选 SIMD）后的最新长区间结果。

最近一轮统一使用：

- 数据集：`data/default`
- 工具长度：`1.0 m`
- 工具半径：`0.025 m`
- 起始深度：`3300 m`
- 截止深度：`3400 m`
- 步长：`0.5 m`
- 运行环境：WSL + Conda 环境 `SWPUCompetiton`

### 2.2 测试对象

#### Python 绑定路径
- Python 原始实现：`python_src/TouYingFa.py` 中的 `Projection2(...)`
- C++ 绑定：`Projection2_cpp(...)`
- C 绑定：`Projection2_c(...)`

#### CLI 路径
- 串行 CLI：默认 `make`
- OpenMP CLI：`make USE_OPENMP=1`

### 2.3 OpenMP 配置

OpenMP 版本分别测试：

- `OMP_NUM_THREADS=1`
- `OMP_NUM_THREADS=4`

---

## 3. 正确性验证

### 3.1 核心结果

所有版本在本次测试参数下得到的核心结果一致：

- `deep = 3308.000000`
- `R = 0.051656160`

### 3.2 差异对比

| 对比项 | 深度差异 (m) | 半径差异 (m) |
|---|---:|---:|
| C++ vs C | `0.000000000` | `0.000000000000` |
| C++ vs Python | `0.000000000` | `0.000000000000` |

### 3.3 结论

本次 benchmark 中：

- Python / C++ / C / OpenMP C 各条路径的核心几何结果完全一致
- OpenMP 并未引入结果漂移
- 并行 tie-break 规则在当前测试中表现稳定

**结论：正确性验证通过。**

---

## 4. Python 绑定路径 Benchmark

### 4.1 串行绑定版本

通过 `scripts/test_cpp_binding.py` 运行，得到如下耗时：

| 版本 | 耗时 (s) | 相对 Python 基线加速比 |
|---|---:|---:|
| Python 原始实现 | `58.552` | `1.0x` |
| C++ 绑定 | `0.241` | `242.6x` |
| C 绑定 | `0.224` | `261.9x` |

### 4.2 OpenMP 绑定版本（1 线程）

OpenMP 编译后，在 `OMP_NUM_THREADS=1` 下测得：

| 版本 | 耗时 (s) | 相对 Python 基线加速比 |
|---|---:|---:|
| Python 原始实现 | `63.591271` | `1.0x` |
| C++ 绑定 | `0.241838` | `262.949896x` |
| C 绑定（OpenMP build, 1 thread） | `0.220527` | `288.360877x` |

### 4.3 OpenMP 绑定版本（4 线程）

OpenMP 编译后，在 `OMP_NUM_THREADS=4` 下测得：

| 版本 | 耗时 (s) | 相对 Python 基线加速比 |
|---|---:|---:|
| Python 原始实现 | `59.612269` | `1.0x` |
| C++ 绑定 | `0.267364` | `222.962741x` |
| C 绑定（OpenMP build, 4 threads） | `0.225686` | `264.138005x` |

### 4.4 Python 绑定路径分析

可以观察到：

1. C++ 与 C 绑定相对 Python 都有两个数量级以上提升
2. C 绑定在本轮测试中略快于 C++ 绑定
3. OpenMP 版 C 后端在 Python 绑定路径下，`1` 线程与 `4` 线程的总耗时差异不明显

这说明：

- 当前测试规模下，Python 调用链、绑定层开销以及其它串行部分，削弱了 OpenMP 在绑定路径中的可见收益
- 但从结果一致性来看，OpenMP 版绑定已可正常工作

---

## 5. CLI 路径 Benchmark

为更准确观察热点优化后原生执行路径的收益，后续对 CLI 单独做了更长区间的 benchmark。

### 5.1 最新长区间 CLI 结果

长区间测试范围：`3300m -> 3400m`，`step=0.5`。

| 版本 | 配置 | 平均耗时 (s) | 相对串行 CLI 加速比 |
|---|---|---:|---:|
| 串行 CLI | 默认 `make` | `1.317` | `1.0x` |
| SIMD CLI | `make USE_SIMD=1` | `0.750` | `1.76x` |
| OpenMP + SIMD CLI | `make USE_OPENMP=1 USE_SIMD=1` | `0.620` | `2.12x` |

此外，最近一次直接实跑的 OpenMP + SIMD CLI 摘要为：

- `总耗时: 0.69s`
- `OpenMP: enabled, 线程数: 12`
- `max_inscribed_circle: 0.52s (75.46%)`
- `get_closest_points: 0.14s (20.76%)`

### 5.2 CLI 路径分析

相较阶段 4 仅 OpenMP 的版本，当前版本进一步叠加了热点标量优化与可选 SIMD：

- 仅启用 SIMD 时，整体已较串行基线提升约 `1.76x`
- OpenMP + SIMD 组合下，整体较串行基线提升约 `2.12x`
- 主收益仍来自 `max_inscribed_circle()`，但其占比已从更早阶段的 `90%+` 压缩到约 `75%`

这说明：

- OpenMP 第一阶段并行化方向是正确的
- 后续针对热点内部做平方距离比较与 SIMD 向量化后，原生 CLI 路径继续获得了稳定收益
- `get_closest_points()` 的相对占比正在上升，已逐渐成为下一阶段值得观察的次热点

---

## 6. 串行 C 路径热点与时间分布分析

### 6.1 分析范围说明

本轮新增了一次**纯 C 串行路径**的阶段级时间分布分析，目标不是继续扩大 OpenMP 范围，而是回答：

- 当前最耗时的函数是谁
- 每个深度窗口时间主要花在哪个阶段
- 下一步优化应优先看哪里

实现方式：

- 保留原有 `row.current_time / row.total_time`
- 在 `c_src/projection_c.c` 的 `projection_c_calculate()` 内围绕现有 helper 调用边界增加阶段计时
- 同时累计轻量计数器（方向数、projected 点数、closest 点数）

### 6.2 本次串行 CLI 实测结果

测试命令：

```bash
make clean && make
./projection_method 1.0 0.025 3300 3350 0.5
```

CLI 摘要输出显示：

| 阶段/指标 | 结果 |
|---|---:|
| 窗口数 | `100` |
| 最大内切圆时间占比 | `92.15%` |
| closest 点提取时间占比 | `6.80%` |
| 平面投影时间占比 | `0.32%` |
| 3D->2D 时间占比 | `0.18%` |
| 平均每窗口方向数 | `173.84` |

### 6.3 热点结论

本次阶段级时间分布给出的高置信结论是：

1. **`max_inscribed_circle()` 是当前绝对主热点**
   - 占总窗口时间约 `92%`
   - 明确是后续继续优化时的第一优先级

2. **`get_closest_points()` 构成第二梯队**
   - 占比约 `6.8%`
   - 若主热点进一步压缩后，这一段会成为下一观察重点

3. **`line_plane_multiple()` 与 `point3d_to_2d()` 当前不是主要瓶颈**
   - 合计占比不到 `1%`
   - 现阶段不应优先投入到这两段的复杂优化

### 6.4 对后续优化的含义

基于这次时间分布分析，后续如果继续推进性能优化，建议优先顺序为：

1. `max_inscribed_circle()`
2. `get_closest_points()`
3. 再评估是否值得扩展到方向循环或其它结构性优化

也就是说，**OpenMP 第一阶段选择并行 `max_inscribed_circle()` 是有数据支撑的，方向是对的。**

---

## 7. 优化效果总结

### 6.1 正向结果

本轮优化已经达到以下目标：

- ✅ 保持 Python / C++ / C 三条路径结果一致
- ✅ OpenMP 版在 macOS 下可正常构建
- ✅ OpenMP 版 Python 绑定可正常导入与运行
- ✅ OpenMP 版 CLI 可正常运行
- ✅ CLI 原生路径下已经观察到稳定加速

### 6.2 当前限制

当前 OpenMP 优化仍属于“第一阶段安全优化”，因此也存在一些自然限制：

1. 只并行了 `max_inscribed_circle()`
2. `projection_c_calculate()` 外层深度循环仍是串行
3. 方向循环仍是串行
4. Python 绑定路径中的整体耗时仍受到绑定调用链影响

因此，当前 benchmark 结果应理解为：

- **OpenMP 已经有效，但优化范围还比较保守**

---

## 7. 结论

本次 benchmark 与后续长区间复测可以得出以下结论：

### 正确性方面
- 所有实现版本输出一致
- OpenMP 版本没有引入数值结果偏差
- 在热点进一步做平方距离比较、延迟 `sqrt` 与可选 SIMD 后，结果仍保持稳定一致

### 性能方面
- 相对串行 CLI 基线：
  - SIMD 路径约 `1.76x`
  - OpenMP + SIMD 路径约 **`2.12x`**
- 最近一次端到端对比中：
  - Python 原始实现约 `226.99s`
  - 最新 OpenMP + SIMD CLI 约 `0.69s`
  - 相对原始 Python 约 **`329x`**

### 最终判断
- **OpenMP 优化版本已经实现并验证通过**
- **在 CLI 原生路径上，OpenMP 与 SIMD 叠加后已体现出更稳定的综合收益**
- **当前主热点仍是 `max_inscribed_circle()`，但 `get_closest_points()` 已逐渐上升为值得继续关注的次热点**

---

## 8. 后续建议

如果后续继续做性能优化，建议按以下顺序推进：

1. 在更大深度范围上重复 benchmark，观察 OpenMP 收益随任务规模变化情况
2. 评估 `grid_num` 对并行收益的影响
3. 进一步分析 `projection_c_calculate()` 中方向循环是否值得做线程私有 buffer 重构
4. 结合 SIMD 或更细粒度算法优化进一步压缩热点时间

---

## 9. 相关文件

- `c_src/projection_c.c`
- `Makefile`
- `cpp_src/python_bindings/setup.py`
- `scripts/test_cpp_binding.py`
- `docs/STAGE4_OPENMP_SUMMARY.md`

---

## 最新性能报告

完整的性能分析、最新 benchmark 数据和各阶段占比，请查看 [AnalysisReport.md](AnalysisReport.md)。
