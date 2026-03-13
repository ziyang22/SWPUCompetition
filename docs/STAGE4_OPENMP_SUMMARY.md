# 阶段 4 完成报告：C 核心 OpenMP 并行优化

## ✅ 完成状态

**阶段 4：C 核心简单 OpenMP 并行优化** - **已完成**

完成时间：2026-03-08

---

## 📋 本次改动目标

本阶段不重构算法主流程，只对纯 C 计算核心做一轮**低风险、可选开启**的 OpenMP 并行优化，目标是：

1. 保持 Python / C++ / C 三条结果链路一致
2. 不改变现有公开接口
3. 默认构建行为不变
4. 在支持 OpenMP 的环境中提供显式 opt-in 并行加速

---

## 🔧 实施内容

### 1. 在 C 核心中加入 OpenMP 条件编译

**修改文件：**
- `c_src/projection_c.c`

**主要改动：**
- 增加 `_OPENMP` 条件编译
- 在启用 OpenMP 时包含 `omp.h`
- 未启用 OpenMP 时保持串行逻辑可正常编译运行

关键位置：
- `c_src/projection_c.c:4`
- `c_src/projection_c.c:392`

### 2. 并行化 `max_inscribed_circle()` 网格搜索

本次只并行了最适合做第一步优化的热点函数：

- `max_inscribed_circle()`

原因：
- 每个网格点 `(i, j)` 的计算相互独立
- 输入点集只读
- 不涉及共享 buffer 扩容
- 易于做线程局部最优值归约

实现方式：
- 使用 OpenMP 并行 `for`
- 每个线程维护自己的最佳候选圆
- 结束后再合并到全局最佳结果

### 3. 增加稳定 tie-break 规则

**新增逻辑：**
- `circle_candidate_better(...)`

作用：
- 避免多个线程在“半径相同或几乎相同”时因为调度顺序不同而选出不同圆心
- 保证并行与串行结果稳定一致

规则：
1. 半径更大者优先
2. 若半径在容差内相同，优先选择更小的网格索引 `(i, j)`

关键位置：
- `c_src/projection_c.c:373`

---

## 🏗️ 构建系统更新

### 1. CLI 构建开关

**修改文件：**
- `Makefile`

**新增能力：**
- `USE_OPENMP ?= 0`
- 默认 `make` 行为不变
- 显式启用时：

```bash
make USE_OPENMP=1
```

### 2. macOS 下的 libomp 处理

本次同时修复了 macOS 的 OpenMP 构建链：

- 自动探测 `brew --prefix libomp`
- 为 `clang/clang++` 添加：
  - `-Xpreprocessor -fopenmp`
  - `-I$(LIBOMP_PREFIX)/include`
  - `-L$(LIBOMP_PREFIX)/lib -lomp`

### 3. Python 绑定构建开关

**修改文件：**
- `cpp_src/python_bindings/setup.py`

**新增能力：**
- 通过环境变量控制是否启用 OpenMP：

```bash
PROJECTION_USE_OPENMP=1 pip install -e .
```

在 macOS 下会自动：
- 探测 `brew --prefix libomp`
- 追加 OpenMP compile/link 参数

---

## ✅ 明确保留不变的部分

本次没有扩大修改范围，以下内容保持不变：

- `projection_c_calculate()` 外层深度循环仍为串行
- 方向循环仍为串行
- 输出文件格式不变
- Python 接口语义不变
- C API 不变
- stop-on-first-stuck 行为不变
- `append_result()` 顺序收集逻辑不变

这保证了本次优化只影响一个局部热点，而不改变整体行为。

---

## 🧪 验证结果

### 1. 默认串行构建

验证通过：

```bash
make clean && make
./projection_method 1.0 0.025 3300 3310 0.5
```

结果：
- ✅ 编译成功
- ✅ CLI 正常运行
- ✅ 输出结果正常

### 2. OpenMP CLI 构建

验证通过：

```bash
make clean && make USE_OPENMP=1
OMP_NUM_THREADS=1 ./projection_method 1.0 0.025 3300 3310 0.5
OMP_NUM_THREADS=4 ./projection_method 1.0 0.025 3300 3310 0.5
```

结果：
- ✅ macOS 下编译成功
- ✅ 1 线程运行正常
- ✅ 4 线程运行正常
- ✅ 几何结果一致

### 3. Python 绑定 OpenMP 构建

验证通过：

```bash
cd cpp_src/python_bindings
PROJECTION_USE_OPENMP=1 pip install -e .
```

结果：
- ✅ Python 扩展安装成功
- ✅ C 后端 OpenMP 构建链打通

### 4. 结果一致性验证

使用：
- `scripts/test_cpp_binding.py`

实测结论：

- `C++ vs C 深度差异: 0.000000 m`
- `C++ vs C 半径差异: 0.000000 m`
- `C++ vs Python 深度差异: 0.000000 m`
- `C++ vs Python 半径差异: 0.000000 m`

结论：
- ✅ OpenMP 改动后，Python / C++ / C 三条路径结果仍保持一致

---

## 🚀 性能观察更新

阶段 4 文档最初记录的是 `3300m -> 3310m` 小范围 OpenMP 验证结果。随着后续继续围绕 `max_inscribed_circle()` 做平方距离比较、延迟 `sqrt` 与可选 SIMD 优化，长区间实测结果已更新为：

### 1. 长区间 CLI benchmark（`3300m -> 3400m`）

| 模式 | 命令 | 平均耗时 |
|------|------|-----------|
| 串行 CLI | 默认 `make` | `1.317s` |
| SIMD CLI | `make USE_SIMD=1` | `0.750s` |
| OpenMP + SIMD CLI | `make USE_OPENMP=1 USE_SIMD=1` | `0.620s` |

### 2. 最近一次端到端对比

- `Python 原始实现`: `226.99s`
- `最新 OpenMP + SIMD CLI`: `0.69s`
- `相对 Python 加速比`: 约 **329x**

### 3. 当前阶段理解

这说明阶段 4 的 OpenMP 并行化不仅本身有效，而且为后续热点内部的标量优化与 SIMD 叠加优化提供了稳定基础：

- OpenMP 方向是正确的
- `max_inscribed_circle()` 仍然是主要热点
- 在当前版本下，OpenMP + SIMD 已经成为更有代表性的推荐性能配置

### 4. 历史小范围结果

以下小范围结果仍保留，作为阶段 4 当时完成时的验证记录：

在 `3300m -> 3310m` 小范围测试中：

| 模式 | 命令 | real 时间 |
|------|------|-----------|
| 串行 CLI | 默认 `make` 构建 | `0.75s` |
| OpenMP CLI（1线程） | `OMP_NUM_THREADS=1` | `0.78s` |
| OpenMP CLI（4线程） | `OMP_NUM_THREADS=4` | `0.22s` |

说明：
- 1 线程时会有少量 OpenMP 开销
- 多线程下该热点已有明显收益
- 更大范围测试下，后续又进一步验证了 SIMD 与 OpenMP+SIMD 的叠加收益

---

## ⚠️ 本阶段踩到的问题

### 1. macOS 编译失败：找不到 `omp.h`

报错：

```text
fatal error: 'omp.h' file not found
```

原因：
- 本机最初未安装 Homebrew `libomp`

解决：

```bash
brew install libomp
```

随后在 `Makefile` 和 `setup.py` 中显式补齐 include/lib 路径。

---

## 📁 受影响文件

### 修改文件
- `c_src/projection_c.c`
- `Makefile`
- `cpp_src/python_bindings/setup.py`

### 新增文档
- `docs/STAGE4_OPENMP_SUMMARY.md`

---

## 🎯 阶段结论

本阶段已经完成一个**简单、稳定、可选开启**的 OpenMP 优化版本：

- ✅ OpenMP 代码已接入纯 C 计算核心
- ✅ 默认串行构建路径不受影响
- ✅ macOS CLI 构建已打通
- ✅ Python 绑定 OpenMP 构建已打通
- ✅ 结果与原 Python / C++ / C 后端保持一致
- ✅ 在多线程下观察到正向性能收益

---

## 🔄 后续可选方向

如果后续继续优化，可考虑：

1. 对更大深度区间做系统性能基准
2. 评估 `grid_num` 与并行收益的关系
3. 再考虑方向循环的线程私有 buffer 设计
4. 评估 SIMD / 算法层面的进一步优化

但这些都属于下一阶段工作，不包含在本次简单 OpenMP 优化范围内。
