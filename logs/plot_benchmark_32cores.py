#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
绘制 Benchmark-32cores.log 中每种方法加速比的折线图
分别绘制不同数据集不同场景的独立图片
"""

import matplotlib.pyplot as plt
import numpy as np

# 配置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# 数据定义 (从 Benchmark-32cores.log 提取)
configurations = [
    'Python\nBaseline',
    'C++\nSerial',
    'C++\n+OpenMP',
    'C++\n+OpenMP+SIMD',
    'C++\n+Adaptive'
]

# Dataset-1 加速比数据
dataset1_cannot_pass = [1.0, 295.4, 4800.3, 4800.3, 249.4]
dataset1_pass = [1.0, 295.4, 4800.3, 4800.3, 2743.0]

# Dataset-2 加速比数据
dataset2_cannot_pass = [1.0, 301.6, 6132.4, 4599.3, 18397.3]
dataset2_pass = [1.0, 301.6, 6132.4, 4599.3, 2628.2]

x = np.arange(len(configurations))

# ============================================================
# 图1: Dataset-1 - cannot_pass
# ============================================================
fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(x, dataset1_cannot_pass, marker='o', markersize=10, linewidth=2.5,
         color='#e74c3c', markerfacecolor='white', markeredgewidth=2)

for i, val in enumerate(dataset1_cannot_pass):
    ax.annotate(f'{val:.1f}x', xy=(i, val), xytext=(0, 5),
                textcoords="offset points", ha='center', va='bottom', fontsize=9, fontweight='bold')

ax.set_xlabel('Configuration', fontsize=12)
ax.set_ylabel('Speedup', fontsize=12)
ax.set_title('Dataset-1: cannot_pass (32 Cores)', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(configurations, fontsize=10)
ax.grid(True, alpha=0.3, linestyle='--')
ax.set_ylim(bottom=0)
ax.set_yticks([0, 1000, 2000, 3000, 4000, 5000])

plt.tight_layout()
output_path1 = '/home/ziyoung/Project/SWPUCompetition/report/Picture/benchmark_32cores_dataset1_cannot_pass.png'
plt.savefig(output_path1, dpi=150, bbox_inches='tight', facecolor='white')
print(f"图片已保存至: {output_path1}")
plt.close()

# ============================================================
# 图2: Dataset-1 - pass
# ============================================================
fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(x, dataset1_pass, marker='s', markersize=10, linewidth=2.5,
         color='#3498db', markerfacecolor='white', markeredgewidth=2)

for i, val in enumerate(dataset1_pass):
    ax.annotate(f'{val:.1f}x', xy=(i, val), xytext=(0, 5),
                textcoords="offset points", ha='center', va='bottom', fontsize=9, fontweight='bold')

ax.set_xlabel('Configuration', fontsize=12)
ax.set_ylabel('Speedup', fontsize=12)
ax.set_title('Dataset-1: pass (32 Cores)', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(configurations, fontsize=10)
ax.grid(True, alpha=0.3, linestyle='--')
ax.set_ylim(bottom=0)
ax.set_yticks([0, 1000, 2000, 3000, 4000, 5000])

plt.tight_layout()
output_path2 = '/home/ziyoung/Project/SWPUCompetition/report/Picture/benchmark_32cores_dataset1_pass.png'
plt.savefig(output_path2, dpi=150, bbox_inches='tight', facecolor='white')
print(f"图片已保存至: {output_path2}")
plt.close()

# ============================================================
# 图3: Dataset-2 - cannot_pass (对数坐标，因为18397.3x是异常值)
# ============================================================
fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(x, dataset2_cannot_pass, marker='^', markersize=10, linewidth=2.5,
         color='#9b59b6', markerfacecolor='white', markeredgewidth=2)
ax.set_yscale('log')

# 对数坐标下调整标注位置
for i, val in enumerate(dataset2_cannot_pass):
    offset = 5 if val < 10000 else -15
    ax.annotate(f'{val:.1f}x', xy=(i, val), xytext=(0, offset),
                textcoords="offset points", ha='center', va='bottom', fontsize=9, fontweight='bold')

ax.set_xlabel('Configuration', fontsize=12)
ax.set_ylabel('Speedup (log scale)', fontsize=12)
ax.set_title('Dataset-2: cannot_pass (32 Cores)', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(configurations, fontsize=10)
ax.grid(True, alpha=0.3, linestyle='--', which='both')

plt.tight_layout()
output_path3 = '/home/ziyoung/Project/SWPUCompetition/report/Picture/benchmark_32cores_dataset2_cannot_pass.png'
plt.savefig(output_path3, dpi=150, bbox_inches='tight', facecolor='white')
print(f"图片已保存至: {output_path3}")
plt.close()

# ============================================================
# 图4: Dataset-2 - pass
# ============================================================
fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(x, dataset2_pass, marker='D', markersize=10, linewidth=2.5,
         color='#f39c12', markerfacecolor='white', markeredgewidth=2)

for i, val in enumerate(dataset2_pass):
    ax.annotate(f'{val:.1f}x', xy=(i, val), xytext=(0, 5),
                textcoords="offset points", ha='center', va='bottom', fontsize=9, fontweight='bold')

ax.set_xlabel('Configuration', fontsize=12)
ax.set_ylabel('Speedup', fontsize=12)
ax.set_title('Dataset-2: pass (32 Cores)', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(configurations, fontsize=10)
ax.grid(True, alpha=0.3, linestyle='--')
ax.set_ylim(bottom=0)
ax.set_yticks([0, 1000, 2000, 3000, 4000, 5000, 6000, 7000])

plt.tight_layout()
output_path4 = '/home/ziyoung/Project/SWPUCompetition/report/Picture/benchmark_32cores_dataset2_pass.png'
plt.savefig(output_path4, dpi=150, bbox_inches='tight', facecolor='white')
print(f"图片已保存至: {output_path4}")
plt.close()

print("\n所有图表已生成完毕!")
