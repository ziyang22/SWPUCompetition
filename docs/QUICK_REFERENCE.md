# 快速参考卡

## 🚀 一键命令

```bash
make test    # 编译 + 运行 + 验证（推荐）
```

---

## 📋 常用命令

### 编译
```bash
make              # 编译
make clean        # 清理
make clean && make # 重新编译
```

### 运行
```bash
./projection_method                           # 默认参数
./projection_method 1.0 0.025 3300 3400 0.5  # 自定义参数
```

### 验证
```bash
conda activate SWPUCompetiton
python scripts/check_output.py
```

---

## 📁 目录结构

```
cpp_src/     - C++ 源代码
scripts/     - Python/Shell 脚本
docs/        - 文档
examples/    - 示例输出
build/       - 构建产物
```

---

## 📖 文档快速链接

| 文档 | 命令 |
|------|------|
| 项目说明 | `cat README.md` |
| 快速开始 | `cat docs/QUICK_START.md` |
| 使用指南 | `cat docs/HOW_TO_USE.md` |
| 项目结构 | `cat PROJECT_STRUCTURE.md` |

---

## 🔧 参数说明

```bash
./projection_method <工具长度> <工具半径> <起始深度> <截止深度> <步长>
                    ↓         ↓         ↓         ↓         ↓
                    1.0       0.025     3300      3400      0.5
                    (m)       (m)       (m)       (m)       (m)
```

---

## 📊 输出文件

### 通过
- `pass_last_5m_3400m.txt`

### 卡点
- `stuck_point_3393m.txt`
- `final_result_3393m.txt`

---

## ⚡ 性能

- Python: ~200-400s
- C++: ~0.06s
- 加速: **3000-6000x**

---

## ✅ 验证结果

```
✓ 深度(m)      - 误差: 0.0
✓ 工具长度(m)  - 误差: 0.0
✓ 圆心X(m)     - 误差: 0.0
✓ 圆心Y(m)     - 误差: 0.0
✓ 直径(m)      - 误差: 0.0
```

---

## 🆘 故障排除

### 编译失败
```bash
g++ --version  # 检查编译器
make clean && make
```

### 找不到文件
```bash
pwd  # 确认在项目根目录
ls all_data.csv Point_3D.npy
```

### 输出不一致
```bash
make clean && make test
```

---

## 📞 获取帮助

```bash
make help                    # Makefile 帮助
cat README.md                # 项目说明
cat PROJECT_COMPLETE.md      # 完整总结
```

---

**快速开始**: `make test`

**项目状态**: 🚀 生产就绪
