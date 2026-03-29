import matplotlib.pyplot as plt
import numpy as np

# Data extracted from benchmark log
methods = [
    'Python Baseline',
    'C++ Serial',
    'C++ + OpenMP',
    'C++ + OpenMP + SIMD',
    'C++ + OpenMP + SIMD + Adaptive'
]

# Speedup data for each dataset/scenario
dataset1_cannot_pass = [1.0, 297.2, 1931.6, 1207.2, 203.3]
dataset1_pass = [1.0, 301.8, 1756.0, 1287.7, 1207.2]
dataset2_cannot_pass = [1.0, 334.2, 2153.7, 1384.5, 9691.5]
dataset2_pass = [1.0, 323.0, 1762.1, 1384.5, 1211.4]

# Use shorter labels for x-axis
short_labels = ['Python', 'Serial', 'OpenMP', 'SIMD', 'Adaptive']

x = np.arange(len(short_labels))
width = 0.2

fig, ax = plt.subplots(figsize=(12, 7))

bars1 = ax.bar(x - 1.5*width, dataset1_cannot_pass, width, label='Dataset-1 cannot_pass', color='#1f77b4')
bars2 = ax.bar(x - 0.5*width, dataset1_pass, width, label='Dataset-1 pass', color='#ff7f0e')
bars3 = ax.bar(x + 0.5*width, dataset2_cannot_pass, width, label='Dataset-2 cannot_pass', color='#2ca02c')
bars4 = ax.bar(x + 1.5*width, dataset2_pass, width, label='Dataset-2 pass', color='#d62728')

ax.set_xlabel('Optimization Method', fontsize=12)
ax.set_ylabel('Speedup (x)', fontsize=12)
ax.set_title('Benchmark Speedup Comparison (6 Cores)', fontsize=14)
ax.set_xticks(x)
ax.set_xticklabels(short_labels, fontsize=11)
ax.legend(loc='upper left', fontsize=10)
ax.set_yscale('log')
ax.grid(True, alpha=0.3, axis='y')

# Add value labels on bars
for bars in [bars1, bars2, bars3, bars4]:
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{height:.0f}x',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=8, rotation=45)

plt.tight_layout()
plt.savefig('/home/ziyoung/Project/SWPUCompetition/logs/speedup_comparison.png', dpi=150)
plt.close()

print("Chart saved to /home/ziyoung/Project/SWPUCompetition/logs/speedup_comparison.png")