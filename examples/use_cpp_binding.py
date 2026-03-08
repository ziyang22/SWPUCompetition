#!/usr/bin/env python3
"""
使用 C++ 加速的投影法计算示例

展示如何在 Python 代码中使用 Projection2_cpp 替代原始的 Projection2
"""

from pathlib import Path

import numpy as np
import pandas as pd
from projection_cpp import Projection2_c, Projection2_cpp

ROOT = Path(__file__).resolve().parent.parent

# 加载数据
print("加载数据...")
all_data = pd.read_csv(ROOT / 'data' / 'default' / 'all_data.csv')
Point_3D = np.load(ROOT / 'data' / 'default' / 'Point_3D.npy')

# 设置参数
instrument_length = 1.0      # 工具长度 (m)
instrument_radius = 0.025    # 工具半径 (m)
begin_deep = 3300            # 起始深度 (m)
end_deep = 3400              # 截止深度 (m)
num_step = 0.5               # 步长 (m)

print(f"\n计算参数:")
print(f"  工具长度: {instrument_length} m")
print(f"  工具半径: {instrument_radius} m")
print(f"  深度范围: {begin_deep} - {end_deep} m")
print(f"  步长: {num_step} m")

# 调用 C++ 实现（与原始 Projection2 接口完全兼容）
print(f"\n开始计算 C++ 后端...")
deep, R, rr, dd, p_all, t_all, draw_R = Projection2_cpp(
    all_data,
    Point_3D,
    instrument_length,
    instrument_radius,
    begin_deep,
    end_deep,
    num_step
)

print(f"\n开始计算 C 后端...")
deep_c, R_c, rr_c, dd_c, p_all_c, t_all_c, draw_R_c = Projection2_c(
    all_data,
    Point_3D,
    instrument_length,
    instrument_radius,
    begin_deep,
    end_deep,
    num_step
)

# 输出结果
print(f"\nC++ 后端计算完成！")
print(f"  卡点深度: {deep:.3f} m")
print(f"  最小半径: {R:.6f} m")
print(f"  最大通过直径: {R * 2 * 1000:.3f} mm")
print(f"  总耗时: {t_all:.3f} 秒")

print(f"\nC 后端计算完成！")
print(f"  卡点深度: {deep_c:.3f} m")
print(f"  最小半径: {R_c:.6f} m")
print(f"  最大通过直径: {R_c * 2 * 1000:.3f} mm")
print(f"  总耗时: {t_all_c:.3f} 秒")

# 判断是否能通过
if R >= instrument_radius:
    print(f"\n✓ 工具可以通过！")
    print(f"  输出文件: output/pass_last_5m_{end_deep}m.txt")
else:
    print(f"\n✗ 工具无法通过，卡在 {deep:.3f} m")
    print(f"  输出文件: output/stuck_point_{int(deep)}m.txt")
    print(f"            output/final_result_{int(deep)}m.txt")
