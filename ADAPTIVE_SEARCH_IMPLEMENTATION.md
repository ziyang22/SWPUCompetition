# 自适应搜索模式实现总结

## 实现概述

本次更新为井眼通过能力计算程序添加了自适应搜索模式，通过动态调整计算步长实现了 17-21 倍的性能提升。

## 修改文件清单

### 1. C 后端核心实现 (`c_src/projection_c.c`)

**修改位置：** 第 638-902 行

**主要改动：**
- 添加 `projection_c_config` 结构体的自适应参数字段
- 实现自适应搜索算法（第 701-902 行）
- 添加智能回溯机制
- 保留原有固定步长模式（向后兼容）

**关键代码段：**
```c
// 配置结构体新增字段
typedef struct {
    // ... 原有字段 ...
    int enable_adaptive;      // 自适应搜索开关
    double growth_factor;     // 步长增长系数
    double min_step;          // 最小步长
    double max_step;          // 最大步长
} projection_c_config;

// 自适应搜索主循环
if (config->enable_adaptive) {
    // 初始化 begin 和 end
    begin = find_depth_index(input, config->begin_deep);
    end = find_depth_index(input, config->end_deep) + 1;

    double current_step = config->num_step;
    int last_passed_idx = begin;
    int search_idx = begin;

    while (search_idx < end - 1) {
        // 计算当前窗口
     // ...

     if (工具无法通过) {
            if (!backtrack_mode && current_step > min_step * 1.5) {
                // 回溯到上一个通过点，使用小步长
                backtrack_mode = 1;
            search_idx = last_passed_idx;
           current_step = min_step;
                continue;
          } else {
                // 确认卡点
          output->stuck_depth = ...;
         break;
            }

        // 通过，增长步长
        last_passed_idx = j;
        search_idx = j;
        if (!backtrack_mode) {
            current_step *= growth_factor;
            if (current_step > max_step) current_step = max_step;
        }
    }
}
```

### 2. C++ 接口层 (`cpp_src/projection_method.h` 和 `.cpp`)

**修改位置：**
- `projection_method.h`: 第 20-30 行（类定义）
- `projection_method.cpp`: 第 50-80 行（calculate 方法）

**主要改动：**
- `ProjectionCalculator` 类添加自适应参数成员变量
- `calculate` 方法添加自适应参数
- 将参数传递给 C 后端

**关键代码段：**
```cpp
class ProjectionCalculator {
private:
    // ... 原有成员 ...
    int enable_adaptive_;
    double growth_factor_;
    double min_step_;
    double max_step_;

public:
    bool calculate(
        double begin_deep,
        double end_deep,
        std::vector<CalculationResult>& results,
        double& stuck_depth,
        double& min_radius,
        int enable_adaptive = 0,
        double growth_factor = 2.0,
        double min_step = 0.5,
      double max_step = 10.0
    );
};
```

### 3. 主程序 (`cpp_src/main.cpp`)

**修改位置：** 第 136-200 行

**主要改动：**
- 添加命令行参数解析（第 6-10 个参数）
- 添加自适应参数输出显示
- 更新 `calculate` 调用传递新参数

**关键代码段：**
```cpp
// 参数声明
int enable_adaptive = 0;
double growth_factor = 2.0;
double min_step = 0.5;
double max_step = 10.0;

// 命令行参数解析
if (argc >= 7) enable_adaptive = std::stoi(argv[6]);
if (argc >= 8) growth_factor = std::stod(argv[7]);
if (argc >= 9) min_step = std::stod(argv[8]);
if (argc >= 10) max_step = std::stod(argv[9]);

// 参数输出
if (enable_adaptive) {
    std::cout << "  自适应搜索: 启用" << std::endl;
    std::cout << "    增长系数: " << growth_factor << std::endl;
    std::cout << "    最小步长: " << min_step << " m" << std::endl;
    std::cout << "    最大步长: " << max_step << " m" << std::endl;
}

// 调用计算
bool passed = calculator.calculate(
    begin_deep, end_deep, results, stuck_depth, min_radius,
    enable_adaptive, growth_factor, min_step, max_step
);
```

### 4. 新增文档

- `ADAPTIVE_SEARCH_GUIDE.md` - 详细使用指南
- `ADAPTIVE_SEARCH_IMPLEMENTATION.md` - 本文档
- `benchmark.sh` - 性能对比测试脚本
- `performance_comparison.txt` - 性能测试结果

### 5. 更新文档

- `README.md` - 添加自适应搜索说明和性能对比

## 算法原理

### 核心思想

在井眼相对平滑的区域使用大步长快速跳过，在检测到潜在卡点时自动回溯并使用小步长精确搜索。
### 算法流程

```
1. 初始化
   - current_step = num_step (初始步长，如 0.5m)
   - search_idx = begin
   - last_passed_idx = begin

2. 主循环 (while search_idx < end)
   a. 计算当前窗口 (search_idx -> search_idx + current_step)

   b. 如果工具可以通过：
      - last_passed_idx = current_idx
      - search_idx = current_idx
      - 如果不在回溯模式：
        * current_step *= growth_factor
      * if current_step > max_step: current_step = max_step

   c. 如果工具无法通过：
      - 如果 current_step > min_step * 1.5 且不在回溯模式：
      * 进入回溯模式
        * search_idx = last_passed_idx
        * current_step = min_step
        * 继续循环
      - 否则：
        * 确认卡点
        * 记录 stuck_depth 和 min_radius
        * 退出循环

3. 完成
   - 如果到达终点：工具可以通过
   - 如果中途退出：工具卡住
```

### 示例执行过程

```
深度范围: 3300m - 3400m
初始步长: 0.5m, 增长系数: 2.0, 最大步长: 10m

迭代 1: 3300.0 -> 3300.5 (0.5m)  ✓ 通过, 步长 -> 1.0m
迭代 2: 3300.5 -> 3301.5 (1.0m)  ✓ 通过, 步长 -> 2.0m
迭代 3: 3301.5 -> 3303.5 (2.0m)  ✓ 通过, 步长 -> 4.0m
迭代 4: 3303.5 -> 3307.5 (4.0m)  ✓ 通过, 步长 -> 8.0m
迭代 5: 3307.5 -> 3315.5 (8.0m)  ✓ 通过, 步长 -> 10.0m (达到最大)
迭代 6: 3315.5 -> 3325.5 (10.0m) ✓ 通过, 步长保持 10.0m
迭代 7: 3325.5 -> 3335.5 (10.0m) ✓ 通过, 步长保持 10.0m
...
迭代 14: 3395.5 -> 3400.0 (10.0m) ✓ 通过, 完成

总计: 14 次迭代 vs 固定步长 200 次
```

## 性能测试结果

### 测试环境
- CPU: 12 核心
- OpenMP: 启用
- 编译器: GCC with -O3 优化

### 测试 1: 小范围 (100m)

```
深度范围: 3300m - 3400m
工具: 长度 1.0m, 半径 0.025m

固定步长模式 (步长 0.5m):
  - 窗口数: 200
  - 总耗时: 1.90s

自适应搜索模式:
  - 窗口数: 14
  - 总耗时: 0.11s
  - 性能提升: 17.3x
  - 窗口减少: 93%
```

### 测试 2: 大范围 (1000m)

```
深度范围: 3000m - 4000m
工具: 长度 1.0m, 半径 0.025m

固定步长模式 (步长 0.5m):
  - 窗口数: 2000
  - 总耗时: 9.28s

自适应搜索模式:
  - 窗口数: 104
  - 总耗时: 0.44s
  - 性能提升: 21.1x
  - 窗口减少: 94.8%
```

### 性能分析

1. **窗口数减少**: 93-95%
   - 大步长快速跳过平滑区域
   - 仅在必要时使用小步长

2. **计算时间减少**: 17-21 倍
   - 与窗口数减少成正比
   - 范围越大，提升越明显

3. **精度保持**:
   - 回溯机制确保卡点精确定位
   - 最小步长保证精度要求

## 向后兼容性

### 完全兼容

所有现有代码和脚本无需修改即可继续使用：

```bash
# 原有调用方式（固定步长模式）
./projection_method 1.0 0.025 3300 3400 0.5

# 等价于
./projection_method 1.0 0.025 3300 3400 0.5 0
```

### 新功能启用

```bash
# 启用自适应搜索（使用默认参数）
./projection_method 1.0 0.025 3300 3400 0.5 1

# 自定义参数
./projection_method 1.0 0.025 3300 3400 0.5 1 2.0 0.5 10.0
```

## 使用建议

### 推荐使用自适应搜索

- ✅ 大范围深度计算（> 500m）
- ✅ 井眼相对平滑的区域
- ✅ 需要快速获得结果
- ✅ 批量计算多个工具尺寸

### 继续使用固定步长

- ⚠️ 小范围计算（< 50m）
- ⚠️ 需要完整的深度-直径曲线
- ⚠️ 研究井眼几何特征变化
- ⚠️ 已知存在多个卡点的复杂井眼

## 参数调优

### 默认参数（推荐）

```
enable_adaptive = 1
growth_factor = 2.0
min_step = 0.5m
max_step = 10.0m
```

### 高精度场景

```
growth_factor = 1.5    # 更保守的增长
min_step = 0.1m        # 更小的最小步长
max_step = 5.0m        # 更小的最大步长
```

### 快速扫描场景

```
growth_factor = 3.0    # 更激进的增长
min_step = 1.0m        # 更大的最小步长
max_step = 20.0m       # 更大的最大步长
```

## 未来改进方向

1. **Python 绑定支持**
   - 在 pybind11 接口中暴露自适应参数
   - 允许 Python 代码使用自适应搜索

2. **交互模式支持**
   - 在交互式输入中添加自适应参数选项

3. **自动参数调优**
   - 根据井眼特征自动选择最优参数
   - 机器学习预测最佳步长策略

4. **多卡点优化**
   - 改进回溯策略处理多个卡点
   - 记录所有潜在卡点位置

5. **可视化输出**
   - 显示步长变化曲线
   - 标注回溯点和卡点位置

## 测试验证

### 功能测试

- ✅ 固定步长模式正常工作
- ✅ 自适应搜索模式正常工作
- ✅ 回溯机制正确触发
- ✅ 卡点精确定位
- ✅ 参数解析正确

### 性能测试

- ✅ 小范围 (100m): 17.3x 提升
- ✅ 大范围 (1000m): 21.1x 提升
- ✅ 窗口数减少 93-95%

### 兼容性测试

- ✅ 原有命令行调用正常
- ✅ 输出格式保持一致
- ✅ 错误处理正确

## 总结

自适应搜索模式的成功实现为井眼通过能力计算带来了显著的性能提升，同时保持了完全的向后兼容性。通过智能的步长调整和回溯机制，在保证计算精度的前提下，实现了 17-21 倍的性能提升。

这次实现展示了算法优化在实际工程中的价值，为后续的进一步优化奠定了基础。
