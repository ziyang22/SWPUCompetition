#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
绘制 Benchmark-6cores.log 中每种方法加速比的折线图
分开绘制不同数据集下不同输入参数的图像
"""

import matplotlib.pyplot as plt
import numpy as np

# 配置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# 数据定义
configurations = [
    'Python\nBaseline',
    'C++\nSerial',
    'C++\n+OpenMP',
    'C++\n+OpenMP+SIMD',
    'C++\n+Adaptive'
]

# Dataset-1 加速比数据
dataset1_cannot_pass = [1.0, 297.2, 1931.6, 1207.2, 203.3]
dataset1_pass = [1.0, 301.8, 1756.0, 1287.7, 1207.2]

# Dataset-2 加速比数据
dataset2_cannot_pass = [1.0, 334.2, 2153.7, 1384.5, 9691.5]
dataset2_pass = [1.0, 323.0, 1762.1, 1384.5, 1211.4]

# 颜色方案
colors = ['#2ecc71', '#3498db', '#e74c3c', '#9b59b6', '#f39c12']
markers = ['o', 's', '^', 'D', 'v']

# 设置图形大小
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

x = np.arange(len(configurations))

# ============================================================
# 图1: Dataset-1 - cannot_pass
# ============================================================
ax1 = axes[0, 0]
ax1.plot(x, dataset1_cannot_pass, marker='o', markersize=10, linewidth=2.5,
         color='#e74c3c', markerfacecolor='white', markeredgewidth=2)

for i, val in enumerate(dataset1_cannot_pass):
    ax1.annotate(f'{val:.1f}x', xy=(i, val), xytext=(0, 5),
                textcoords="offset points", ha='center', va='bottom', fontsize=8, fontweight='bold')

ax1.set_xlabel('Configuration', fontsize=11)
ax1.set_ylabel('Speedup', fontsize=11)
ax1.set_title('Dataset-1: cannot_pass', fontsize=13, fontweight='bold')
ax1.set_xticks(x)
ax1.set_xticklabels(configurations, fontsize=9)
ax1.grid(True, alpha=0.3, linestyle='--')
ax1.set_ylim(bottom=0)

# ============================================================
# 图2: Dataset-1 - pass
# ============================================================
ax2 = axes[0, 1]
ax2.plot(x, dataset1_pass, marker='s', markersize=10, linewidth=2.5,
         color='#3498db', markerfacecolor='white', markeredgewidth=2)

for i, val in enumerate(dataset1_pass):
    ax2.annotate(f'{val:.1f}x', xy=(i, val), xytext=(0, 5),
                textcoords="offset points", ha='center', va='bottom', fontsize=8, fontweight='bold')

ax2.set_xlabel('Configuration', fontsize=11)
ax2.set_ylabel('Speedup', fontsize=11)
ax2.set_title('Dataset-1: pass', fontsize=13, fontweight='bold')
ax2.set_xticks(x)
ax2.set_xticklabels(configurations, fontsize=9)
ax2.grid(True, alpha=0.3, linestyle='--')
ax2.set_ylim(bottom=0)

# ============================================================
# 图3: Dataset-2 - cannot_pass (需要对数坐标，因为9691.5x是异常值)
# ============================================================
ax3 = axes[1, 0]
ax3.plot(x, dataset2_cannot_pass, marker='^', markersize=10, linewidth=2.5,
         color='#9b59b6', markerfacecolor='white', markeredgewidth=2)
ax3.set_yscale('log')

for i, val in enumerate(dataset2_cannot_pass):
    offset = 5 if val < 10000 else -15
    ax3.annotate(f'{val:.1f}x', xy=(i, val), xytext=(0, offset),
                textcoords="offset points", ha='center', va='bottom', fontsize=8, fontweight='bold')

ax3.set_xlabel('Configuration', fontsize=11)
ax3.set_ylabel('Speedup (log scale)', fontsize=11)
ax3.set_title('Dataset-2: cannot_pass', fontsize=13, fontweight='bold')
ax3.set_xticks(x)
ax3.set_xticklabels(configurations, fontsize=9)
ax3.grid(True, alpha=0.3, linestyle='--', which='both')

# ============================================================
# 图4: Dataset-2 - pass
# ============================================================
ax4 = axes[1, 1]
ax4.plot(x, dataset2_pass, marker='D', markersize=10, linewidth=2.5,
         color='#f39c12', markerfacecolor='white', markeredgewidth=2)

for i, val in enumerate(dataset2_pass):
    ax4.annotate(f'{val:.1f}x', xy=(i, val), xytext=(0, 5),
                textcoords="offset points", ha='center', va='bottom', fontsize=8, fontweight='bold')

ax4.set_xlabel('Configuration', fontsize=11)
ax4.set_ylabel('Speedup', fontsize=11)
ax4.set_title('Dataset-2: pass', fontsize=13, fontweight='bold')
ax4.set_xticks(x)
ax4.set_xticklabels(configurations, fontsize=9)
ax4.grid(True, alpha=0.3, linestyle='--')
ax4.set_ylim(bottom=0)

# 调整布局
plt.suptitle('Benchmark Results: Speedup Comparison (6 Cores)', fontsize=15, fontweight='bold', y=1.02)
plt.tight_layout()

# 保存图片
output_path = '/home/ziyoung/Project/SWPUCompetition/logs/benchmark_6cores_speedup.png'
plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
print(f"图片已保存至: {output_path}")