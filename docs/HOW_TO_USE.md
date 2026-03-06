# 使用指南

## 快速开始（3 步）

### 1. 编译
```bash
make
```

### 2. 运行
```bash
./projection_method
```

### 3. 验证
```bash
conda activate SWPUCompetiton
python check_output.py
```

就这么简单！

---

## 自定义参数

### 修改计算参数

```bash
./projection_method <工具长度> <工具半径> <起始深度> <截止深度> <步长>
```

**示例**：
```bash
# 工具长度 1m，半径 0.025m，深度 3300-3400m，步长 0.5m
./projection_method 1.0 0.025 3300 3400 0.5

# 测试更大的工具半径（可能卡住）
./projection_method 1.0 0.05 3300 3400 0.5
```

---

## 输出文件

### 通过情况
- `pass_last_5m_3400m.txt` - 最后 5 米的计算数据

### 卡点情况
- `stuck_point_3393m.txt` - 卡点前 5 米数据
- `final_result_3393m.txt` - 卡点摘要

---

## 常用命令

### 清理并重新编译
```bash
make clean && make
```

### 运行并保存日志
```bash
./projection_method 2>&1 | tee output.log
```

### 性能对比
```bash
conda activate SWPUCompetiton
python benchmark.py
```

### 对比特定文件
```bash
conda activate SWPUCompetiton
python compare_cpp_py.py pass_last_5m_3400m.txt PassedExample/pass_last_5m_3400m.txt
```

---

## 故障排除

### 问题：编译失败
```bash
# 检查编译器版本
g++ --version  # 需要支持 C++17

# 尝试使用 clang++
make clean
CXX=clang++ make
```

### 问题：找不到输入文件
```bash
# 确保在正确的目录
pwd
ls all_data.csv Point_3D.npy
```

### 问题：输出不一致
```bash
# 重新编译
make clean && make

# 重新运行
./projection_method 1.0 0.025 3395 3400 0.5

# 验证
python check_output.py
```

---

## 性能提示

### 最大优化编译
```bash
make clean
CXXFLAGS="-O3 -march=native -flto" make
```

### 计时运行
```bash
time ./projection_method 1.0 0.025 3300 3400 0.5
```

---

## 更多信息

- 详细文档：[README.md](README.md)
- 快速开始：[QUICK_START.md](QUICK_START.md)
- 编译指南：[COMPILE_GUIDE.md](COMPILE_GUIDE.md)
- Bug 修复：[BUG_FIX_SUMMARY.md](BUG_FIX_SUMMARY.md)

---

**需要帮助？** 查看文档或检查 [FINAL_SUMMARY.md](FINAL_SUMMARY.md)
